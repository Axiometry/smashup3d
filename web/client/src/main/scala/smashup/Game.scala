package smashup

import scala.scalajs.js
import org.scalajs.dom
import org.denigma.threejs
import org.denigma.threejs.THREE

import scala.scalajs.js.JSON
import org.scalajs.jquery.{jQuery, JQuery}
import scala.scalajs.js.annotation.JSExport

case class Game(players: List[Player], cards: List[Card]) {
  private[this] val playersByName = players.map(p => (p.name, p)).toMap
  private[this] val cardsById = cards.map(c => (c.id, c)).toMap

  def player(name: String) = playersByName(name)
  def card(id: Int) = cardsById(id)
}
case class GameState(game: Game, playerStates: Map[Player, PlayerState], cardStates: Map[Card, CardState], turn: TurnState)
case class TurnState(player: PlayerState, minionsLeft: Int, actionsLeft: Int)
case class Player(name: String, isSelf: Boolean)
trait Card {
  def id: Int
  def name: String
  def text: String
}

case class BaseCard(id: Int, name: String, text: String, powerThreshold: Int, awardPoints: Seq[Int]) extends Card
trait PlayerCard extends Card {
  def player: Player
}
case class MinionCard(id: Int, name: String, text: String, player: Player, power: Int) extends PlayerCard
case class ActionCard(id: Int, name: String, text: String, player: Player) extends PlayerCard

trait CardState {
  def card: Card
}
object CardState {
  trait PlayerCardState extends CardState {
    def card: PlayerCard
  }
  trait InPlayState extends PlayerCardState {
    def owner: Player
  }
  trait OnBaseState extends InPlayState {
    def base: BaseCard
  }
  trait OnMinionState extends InPlayState {
    def minion: MinionCard
  }
  case class MinionOnBaseState(card: MinionCard, owner: Player, base: BaseCard, power: Int, actions: List[ActionCard]) extends OnBaseState
  case class ActionOnBaseState(card: ActionCard, owner: Player, base: BaseCard) extends OnBaseState
  case class ActionOnMinionState(card: ActionCard, owner: Player, minion: MinionCard) extends OnMinionState
  case class InHandState(card: PlayerCard) extends PlayerCardState
  case class InDeckState(card: PlayerCard) extends PlayerCardState
  case class InDiscardState(card: PlayerCard) extends PlayerCardState
  trait BaseCardState {
    def card: BaseCard
  }
  case class BaseInPlayState(card: BaseCard, powerThreshold: Int, actions: List[ActionCard], minions: List[MinionCard]) extends BaseCardState
  case class BaseInDeckState(card: BaseCard) extends BaseCardState
  case class BaseInDiscardState(card: BaseCard) extends BaseCardState
}
case class PlayerState(player: Player, points: Int, handSize: Int, discard: List[Card])



class SmashupHandler {
  import Bootstrap._
  import smashup.{DynamicConversions, dynamicAsInt, dynamicAsString}

  val requests = collection.mutable.Map[Int, Request]()
  val socket = new dom.WebSocket("ws://127.0.0.1:25565/")
  def socketMessage(event: dom.MessageEvent) = {
    dom.console.log(event.data.getClass().getName())
    dom.console.log(event.data.asInstanceOf[String])
    val message = JSON.parse(event.data.asInstanceOf[String])
    val packet = readPacket(message)
    dom.console.log("Received: " + packet)
    packet match {
      case RequestSelectionPacket(request) =>
        requests(request.id) = request
        jQuery("#request_dialog_title").text(request.text)
        jQuery("#request_dialog_body").empty()
        for(option <- request.options) {
          val text = option match {
            case Request.DeckOption(_, deckName) => s"Deck: $deckName"
            case Request.CardOption(_, cardId) => s"Card: $cardId"
            case Request.TextOption(_, t) => t
            case _ => option.toString
          }
          jQuery("#request_dialog_body").append(
            s"""<button type="button" class="btn btn-primary btn-block"
               |     onclick="smashup.Game().handler.makeSelection(${request.id}, ${option.id});">$text</button>
            """.stripMargin)
        }
        jQuery("#request_dialog").modal("show")
      case _ =>
    }
  }
  socket.onmessage = socketMessage _
  socket.onopen = (event: dom.Event) => sendPacket(AuthPacket("testing"))

  def sendPacket(packet: Packet): Unit = {
    val message = writePacket(packet)
    dom.console.log("Sent: " + packet)
    socket.send(JSON.stringify(message))
  }

  @JSExport
  def makeSelection(requestId: Int, optionId: Int): Unit = {
    jQuery("#request_dialog").modal("hide")
    val request = requests(requestId)
    val option = request.options.find(_.id == optionId).get
    requests.remove(requestId)
    sendPacket(ReplySelectionPacket(request, option))
  }

  case class Request(id: Int, text: String, options: Array[Request.Option])
  object Request {
    trait Option {
      def id: Int
    }
    case class DeckOption(id: Int, deckName: String) extends Option
    case class CardOption(id: Int, cardId: Int) extends Option
    case class TextOption(id: Int, text: String) extends Option
  }

  trait Packet
  case class AuthPacket(name: String) extends Packet
  case class JoinGamePacket(gameId: Int) extends Packet
  case class RequestSelectionPacket(request: Request) extends Packet
  case class ReplySelectionPacket(request: Request, option: Request.Option) extends Packet

  def readPacket(data: js.Dynamic): Packet = data.__packet_name.toString match {
    case "join_game" => JoinGamePacket(data.game_id.asInstanceOf[Int])
    case "request_selection" =>
      val opts: Array[Request.Option] = for(opt <- data.options.asInstanceOf[js.Array[js.Dynamic]].to[Array]) yield opt.`type`.toString match {
        case "deck" => Request.DeckOption(opt.id, opt.deck_name)
        case "card" => Request.CardOption(opt.id, opt.card_id)
        case "text" => Request.TextOption(opt.id, opt.text)
      }
      RequestSelectionPacket(Request(data.request_id, data.text, opts))
  }
  def writePacket(packet: Packet): js.Dynamic = packet match {
    case AuthPacket(name) => js.Dynamic.literal(__packet_name = "auth", name = name)
    case ReplySelectionPacket(request: Request, option: Request.Option) =>
      js.Dynamic.literal(__packet_name = "reply_selection", request_id = request.id, option_id = option.id)
  }
}
