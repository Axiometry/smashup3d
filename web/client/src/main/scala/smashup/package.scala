import org.scalajs.dom

import scala.scalajs.js

package object smashup {
  implicit class DynamicConversions(dyn: js.Dynamic) {
    def as[T]: T = dyn.asInstanceOf[T]

    def asArray: js.Array[js.Dynamic] = dyn.asInstanceOf[js.Array[js.Dynamic]]
  }

  implicit def dynamicAsString(dyn: js.Dynamic): String = dyn.asInstanceOf[String]
  implicit def dynamicAsInt(dyn: js.Dynamic): Int = dyn.asInstanceOf[Int]

  def findVariable[T](v: Any, names: String*): T = {
    val dynamic = v.asInstanceOf[js.Dynamic]
    for(name <- names; r = dynamic.selectDynamic(name))
      if(!js.isUndefined(r))
        return r.asInstanceOf[T]
    throw new Error("Undefined variable: ["+names.mkString+"]")
  }
}

/*

				new THREE.LineBasicMaterial({
					color: 0xffffff,
					transparent: true,
					opacity: 0.5
				})
				new THREE.MeshPhongMaterial({
					color: 0x156289,
					emissive: 0x072534,
					side: THREE.DoubleSide,
					shading: THREE.FlatShading
				})
 */