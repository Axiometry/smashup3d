package smashup

import org.scalajs.dom

import scala.scalajs.js
import scala.scalajs.js.JSON

final case class Protocol(host: String, port: Int, path: String = "/",
                          encoders: List[Protocol.PacketEncoder],
                          decoders: List[Protocol.PacketDecoder],
                          listener: Protocol.Listener) {
  import Protocol._
  private val socket = new dom.WebSocket(s"ws://$host:$port$path")
  private val encodersByClass: Map[Class[_], PacketEncoder] = encoders.map(s => (s.packetClass, s)).toMap
  private val decodersByName: Map[String, PacketDecoder] = decoders.map(s => (s.packetName, s)).toMap

  private def onOpen(event: dom.Event) = listener.onOpen()
  private def onClose(event: dom.Event) = listener.onClose()
  private def onMessage(event: dom.MessageEvent) = event.data match {
    case s: String =>
      val json = JSON.parse(s)
      val packetName = json.__packetName.asInstanceOf[String]
      if(decodersByName.contains(packetName)) {
        val packet = decodersByName(packetName).decode(json)
        listener.onPacket(packet)
      }// else
    // TODO error bad packet
    case _ => // TODO error bad packet data
  }
  socket.onopen = onOpen _
  socket.onmessage = onMessage _
  socket.onclose = onClose _
  socket.onerror = onClose _

  def sendPacket(packet: Packet): Unit = {
    val encoder = encodersByClass(packet.getClass)
    val data = encoder.encode(packet.asInstanceOf[encoder.PacketType])
    data.__packet_name = encoder.packetName
    socket.send(JSON.stringify(data))
  }
}
object Protocol {
  trait Listener {
    def onOpen()
    def onPacket(packet: Packet)
    def onClose()
  }

  trait Packet

  trait PacketCoder {
    type PacketType <: Packet
    def packetClass: Class[PacketType]
    def packetName: String
  }
  trait PacketEncoder extends PacketCoder {
    def encode(packet: PacketType): js.Dynamic
  }
  trait PacketDecoder extends PacketCoder {
    def decode(data: js.Dynamic): PacketType
  }
}
object SmashupProtocol {
  import Protocol.{Packet, PacketEncoder, PacketDecoder}
  import smashup.{DynamicConversions, dynamicAsInt, dynamicAsString}

  abstract class AbstractPacketEncoder[PP <: Packet](val packetClass: Class[PP], val packetName: String) extends PacketEncoder { override type PacketType = PP }
  abstract class AbstractPacketDecoder[PP <: Packet](val packetClass: Class[PP], val packetName: String) extends PacketDecoder { override type PacketType = PP }

  case class AuthPacket(name: String) extends Packet
  class AuthPacketEncoder extends AbstractPacketEncoder(classOf[AuthPacket], "auth") {
    override def encode(packet: AuthPacket): js.Dynamic = js.Dynamic.literal(name = packet.name)
  }

  case class JoinGamePacket(gameId: Int) extends Packet
  class JoinGamePacketDecoder extends AbstractPacketDecoder(classOf[JoinGamePacket], "join_game") {
    override def decode(data: js.Dynamic): JoinGamePacket = JoinGamePacket(data.game_id)
  }

  trait RequestOption {
    def id: Int
  }
  case class CardRequestOption(id: Int, cardId: Int) extends RequestOption
  case class DeckRequestOption(id: Int, deckName: String) extends RequestOption
  case class TextRequestOption(id: Int, text: String) extends RequestOption
  case class RequestSelectionPacket(requestId: Int, text: String, options: List[RequestOption]) extends Packet
  class RequestSelectionPacketDecoder extends AbstractPacketDecoder(classOf[RequestSelectionPacket], "request_selection") {
    override def decode(data: js.Dynamic): RequestSelectionPacket = {
      val options = for(opt <- data.options.asArray.to[List]) yield opt.`type`.as[String] match {
        case "deck" => DeckRequestOption(opt.id, opt.deck_name)
        case "card" => CardRequestOption(opt.id, opt.card_id)
        case "text" => TextRequestOption(opt.id, opt.text)
      }
      RequestSelectionPacket(data.request_id, data.text, options)
    }
  }

  case class ReplySelectionPacket(requestId: Int, optionId: Int) extends Packet
  class ReplySelectionPacketEncoder extends AbstractPacketEncoder(classOf[ReplySelectionPacket], "reply_selection") {
    override def encode(packet: ReplySelectionPacket): js.Dynamic =
      js.Dynamic.literal(request_id = packet.requestId, option_id = packet.optionId)
  }
}