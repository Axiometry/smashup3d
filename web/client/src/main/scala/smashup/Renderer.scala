package smashup

import org.scalajs.dom

import org.denigma.threejs
import org.denigma.threejs.THREE

import scala.scalajs.js

class Renderer {
  private val renderer = new threejs.WebGLRenderer(js.Dynamic.literal(antialias = true).asInstanceOf[threejs.WebGLRendererParameters])
  renderer.setSize(640, 480)
  private var renderFunc = defaultRenderFunc

  private def defaultRenderFunc = {
    val ViewAngle = 50
    val Aspect = renderer.domElement.width/renderer.domElement.height.toDouble
    val Near = 0.1
    val Far = 10000
    val CardThickness = 0.3

    val canvasContainer = dom.document.getElementById("gameCanvas")

    val scene = new threejs.Scene()
    val textureLoader = new threejs.TextureLoader()

    val camera = new threejs.PerspectiveCamera(ViewAngle, Aspect, Near, Far)
    val controls = new PointerLockControls(canvasContainer, camera)
    val cameraObject = controls.cameraObject
    cameraObject.position.z = 320
    scene.add(cameraObject)

    val pointLight = new threejs.PointLight(0xF8D898)
    pointLight.position.x = -1000
    pointLight.position.y = 0
    pointLight.position.z = 1000
    pointLight.intensity = 2.9
    pointLight.distance = 10000
    scene.add(pointLight)

    val planeMaterial = new threejs.MeshLambertMaterial()
    planeMaterial.color = new threejs.Color(0x4BD121)
    //planeMaterial.wireframe = true
    val plane = new threejs.Mesh(new threejs.PlaneGeometry(400, 200, 10, 10), planeMaterial)
    plane.receiveShadow = true
    scene.add(plane)

    val pillarMaterial = new threejs.MeshLambertMaterial()
    pillarMaterial.color = new threejs.Color(0x4BD121)
    val pillar = new threejs.Mesh(new threejs.CylinderGeometry(10, 10, 30, 6, 6, false), pillarMaterial)
    pillar.position.x = 100
    pillar.position.y = 100
    scene.add(pillar)

    val loader = new threejs.ObjectLoader()

    var table: threejs.Object3D = null
    loader.load("/assets/models/table.json", (obj: threejs.Object3D) => {
      dom.console.log("Loaded the table! "+obj.position.x+","+obj.position.y+","+obj.position.z)
      val bb = new threejs.Box3().setFromObject(obj)
      dom.console.log("Table size: "+(bb.max.x-bb.min.x)+","+(bb.max.y-bb.min.y)+","+(bb.max.z-bb.min.z))
      obj.position.set(400, 0, 400)
      obj.scale.set(400, 400, 400)
      table = obj
      scene.add(table)
    })

    val cardBackMat = new threejs.MeshPhongMaterial()
    textureLoader.load("assets/images/card_back.jpg", (t: threejs.Texture) => { cardBackMat.map = t; cardBackMat.needsUpdate = true })

    def createCard(name: String) = {
      val w = 25
      val h = 40
      val l = CardThickness
      val cardObj = new threejs.Object3D()
      val mat = new threejs.MeshPhongMaterial()
      textureLoader.load("assets/images/"+name, (t: threejs.Texture) => { mat.map = t; mat.needsUpdate = true })
      val cardPlane = new threejs.Mesh(new threejs.PlaneGeometry(25, 40, 20, 40), mat)
      cardObj.add(cardPlane)

      val cardBack = new threejs.Mesh(new threejs.PlaneGeometry(w, h, 1, 1), cardBackMat)
      cardBack.rotateY(math.Pi)
      cardBack.position.z = -l
      cardObj.add(cardBack)

      val cardSideMat = new threejs.MeshPhongMaterial()
      cardSideMat.color = new threejs.Color(0x555555)

      val cardSideTop = new threejs.Mesh(new threejs.PlaneGeometry(w, l, 1, 1), cardSideMat)
      cardSideTop.rotateX(-math.Pi/2)
      cardSideTop.position.set(0, h/2.0, -l/2.0)
      cardObj.add(cardSideTop)

      val cardSideBottom = new threejs.Mesh(new threejs.PlaneGeometry(w, l, 1, 1), cardSideMat)
      cardSideBottom.rotateX(math.Pi/2)
      cardSideBottom.position.set(0, -h/2.0, -l/2.0)
      cardObj.add(cardSideBottom)

      val cardSideLeft = new threejs.Mesh(new threejs.PlaneGeometry(l, h, 1, 1), cardSideMat)
      cardSideLeft.rotateY(-math.Pi/2)
      cardSideLeft.position.set(-w/2.0, 0, -l/2.0)
      cardObj.add(cardSideLeft)

      val cardSideRight = new threejs.Mesh(new threejs.PlaneGeometry(l, h, 1, 1), cardSideMat)
      cardSideRight.rotateY(math.Pi/2)
      cardSideRight.position.set(w/2.0, 0, -l/2.0)
      cardObj.add(cardSideRight)

      cardObj
    }
    val cardNames = List("augmentation.jpg", "cannon.jpg", "Dinosaurs_KingRex.jpg", "armorstego.jpg", "sacrifice.jpg")
    var cardOff = 0
    for(card <- cardNames) {
      val cardObj = createCard(card)

      cardObj.position.x = cardOff
      cardObj.position.z = 100
      cardOff += 30

      scene.add(cardObj)
    }

    for(i <- 0 to 20) {
      val card = createCard("augmentation.jpg")
      card.position.x = cardOff
      card.position.z = 100+(i*(CardThickness+0.1))
      scene.add(card)
    }

    var oldWidth = 640.0
    var oldHeight = 480.0

    var keyForward, keyBackward, keyLeft, keyRight, keyUp, keyDown = false
    dom.document.addEventListener("keydown", (e: dom.KeyboardEvent) => e.keyCode match {
      case 87 /*W*/ =>
        keyForward = true
      case 83 /*S*/ =>
        keyBackward = true
      case 65 /*A*/ =>
        keyLeft = true
      case 68 /*D*/ =>
        keyRight = true
      case 32 /*Space*/ =>
        keyUp = true
      case 16 /*ShL*/ =>
        keyDown = true
      case 70 =>
        cameraObject.position.set(0, 0, 0)
      case _ =>
    }, false)
    dom.document.addEventListener("keyup", (e: dom.KeyboardEvent) => e.keyCode match {
      case 87 /*W*/ =>
        keyForward = false
      case 83 /*S*/ =>
        keyBackward = false
      case 65 /*A*/ =>
        keyLeft = false
      case 68 /*D*/ =>
        keyRight = false
      case 32 /*Space*/ =>
        keyUp = false
      case 16 /*ShL*/ =>
        keyDown = false
      case _ =>
    }, false)

    (partial: Double) => {
      var vx, vy, vz = 0.0
      if(keyForward) vz -= 1
      if(keyBackward) vz += 1
      if(keyLeft) vx -= 1
      if(keyRight) vx += 1
      if(keyUp) vy += 1
      if(keyDown) vy -= 1
      cameraObject.translateX(5*vx)
      cameraObject.translateY(5*vy)
      cameraObject.translateZ(5*vz)
      val rect = canvasContainer.getBoundingClientRect()
      if(oldWidth != rect.width || oldHeight != rect.height) {
        oldWidth = rect.width
        oldHeight = rect.height
        camera.aspect = oldWidth/oldHeight.toDouble
        camera.updateProjectionMatrix()
        renderer.setSize(rect.width, rect.height)
      }
      renderer.render(scene, camera)
    }
  }

  def canvas = renderer.domElement

  def renderGameState(gameState: GameState) = {

  }

  private def draw(partial: Double): Unit = {
    renderFunc(partial)
    dom.window.requestAnimationFrame(draw _)
  }

  draw(0)
}

class PointerLockControls(target: dom.Element, camera: threejs.Camera) {
  camera.rotation.set(0, 0, 0)

  val pitchObject = new threejs.Object3D()
  pitchObject.add(camera)

  val yawObject = new threejs.Object3D()
  yawObject.position.y = 10
  yawObject.add(pitchObject)

  val pi2 = math.Pi/2

  private val mouseUpFunc: js.Function1[dom.MouseEvent, _] = (event: dom.MouseEvent) => {
    if(!isLocked) {
      val requestFullScreen = findVariable[js.Dynamic](target,
        "requestFullScreen", "mozRequestFullScreen", "webkitRequestFullScreen")
      val requestPointerLock = findVariable[js.Dynamic](target,
        "requestPointerLock", "mozRequestPointerLock", "webkitRequestPointerLock")
      requestFullScreen.call(target)
      requestPointerLock.call(target)
    }
  }
  private val mouseMoveFunc: js.Function1[dom.MouseEvent, _] = (event: dom.MouseEvent) => {
    val movementX = findVariable[Double](event, "movementX", "mozMovementX", "webkitMovementX")
    val movementY = findVariable[Double](event, "movementY", "mozMovementY", "webkitMovementY")

    yawObject.rotation.y -= movementX * 0.002
    pitchObject.rotation.x -= movementY * 0.002

    pitchObject.rotation.x = math.max(-pi2, math.min(pi2, pitchObject.rotation.x))
  }
  private val pointerLockChangeFunc: js.Function1[Any, _] = (event: Any) => {
    if(isLocked)
      attach()
    else
      detach()
  }

  target.addEventListener("mouseup", mouseUpFunc, false)
  dom.document.addEventListener("pointerlockchange", pointerLockChangeFunc, false)
  dom.document.addEventListener("mozpointerlockchange", pointerLockChangeFunc, false)
  dom.document.addEventListener("webkitpointerlockchange", pointerLockChangeFunc, false)

  def isLocked: Boolean = {
    val pointerLockElem = findVariable[dom.Element](dom.document,
      "pointerLockElement", "mozPointerLockElement", "webkitPointerLockElement")
    pointerLockElem == target
  }
  def cameraObject = yawObject
  def attach(): Unit = {
    target.parentNode.addEventListener("mousemove", mouseMoveFunc, false)
  }
  def detach(): Unit = {
    target.parentNode.removeEventListener("mousemove", mouseMoveFunc, false)
  }
  def dispose(): Unit = {
    detach()
    target.removeEventListener("mouseup", mouseUpFunc, false)
    dom.document.removeEventListener("pointerlockchange", pointerLockChangeFunc, false)
    dom.document.removeEventListener("mozpointerlockchange", pointerLockChangeFunc, false)
    dom.document.removeEventListener("webkitpointerlockchange", pointerLockChangeFunc, false)
    pitchObject.remove(camera)
  }
}
