import sbt.Project.projectToRef
import sbt.project

val projectVersion = "0.1-SNAPSHOT"

name := "smashup-online"
version := projectVersion

lazy val server = (project in file("server")).settings(
  //name := "smashup-online-server",
  //version := projectVersion,
  scalaVersion := "2.11.8",
  scalaJSProjects := Seq(client),
  pipelineStages := Seq(scalaJSProd, gzip),
  includeFilter in (Assets, LessKeys.less) := "*.less",
  excludeFilter in (Assets, LessKeys.less) := "_*.less",
  resolvers += sbt.Resolver.bintrayRepo("scalaz", "releases"),
  resolvers += sbt.Resolver.bintrayRepo("bintray", "jcenter"),
  libraryDependencies ++= Seq(
    "com.vmunier" %% "play-scalajs-scripts" % "0.4.0",
    "org.webjars" % "jquery" % "1.11.1",
    "org.webjars" % "three.js" % "r74",
    "org.webjars" % "bootstrap" % "3.3.6",
    "com.lihaoyi" %% "scalatags" % "0.5.4"
  ),
  herokuAppName in Compile := "my-app",
  herokuSkipSubProjects in Compile := false
).enablePlugins(PlayScala).
  aggregate(projectToRef(client)).
  dependsOn(sharedJvm)

lazy val client = (project in file("client")).settings(
  scalaVersion := "2.11.8",
  persistLauncher := false,
  persistLauncher in Test := false,
  resolvers += sbt.Resolver.bintrayRepo("denigma", "denigma-releases"),
  libraryDependencies ++= Seq(
    "org.scala-js" %%% "scalajs-dom" % "0.9.0",
    "org.denigma" %%% "threejs-facade" % "0.0.74-0.1.6",
    "be.doeraene" %%% "scalajs-jquery" % "0.9.0",
    "com.lihaoyi" %%% "scalatags" % "0.5.4"
  )
).enablePlugins(ScalaJSPlugin, ScalaJSPlay).
  dependsOn(sharedJs)

lazy val shared = (crossProject.crossType(CrossType.Pure) in file("shared")).
  settings(scalaVersion := "2.11.8").
  jsConfigure(_ enablePlugins ScalaJSPlay)

lazy val sharedJvm = shared.jvm
lazy val sharedJs = shared.js

onLoad in Global := (Command.process("project server", _: State)) compose (onLoad in Global).value
