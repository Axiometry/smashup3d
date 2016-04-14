package smashup

import org.scalajs.dom

class Smashup {
  dom.document.getElementById("state").textContent = "Loading..."

  var gameState: Option[GameState] = None
  val renderer = new Renderer()
  dom.document.getElementById("gameCanvas").appendChild(renderer.canvas)

  dom.document.getElementById("state").textContent = "Loaded."
}