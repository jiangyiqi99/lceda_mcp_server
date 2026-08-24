#!/usr/bin/env node

import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import vm from "node:vm";

const workspaceRoot = path.resolve(import.meta.dirname, ".");
const defaultAppRoot = path.join(workspaceRoot, "嘉立创EDA(专业版).app");
const args = process.argv.slice(2);
const dryRun = args.includes("--dry-run");
const positionalArgs = args.filter((arg) => !arg.startsWith("--"));
const appRoot = path.resolve(positionalArgs[0] || defaultAppRoot);

function sha256(data) {
  return crypto.createHash("sha256").update(data).digest("hex");
}

function shortPathHash(value) {
  return crypto.createHash("sha256").update(value).digest("hex").slice(0, 12);
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function findResourceRoot(root) {
  const candidates = [
    root,
    path.join(root, "Contents", "Resources", "app"),
    path.join(root, "resources", "app"),
    path.join(root, "Resources", "app"),
  ];
  for (const candidate of candidates) {
    if (
      fs.existsSync(path.join(candidate, "assets")) &&
      fs.existsSync(path.join(candidate, "package.json"))
    ) {
      return candidate;
    }
  }
  throw new Error(
    `Cannot locate the EDA resource root below: ${root}. ` +
      "Pass the .app/application directory or its resources/app directory.",
  );
}

function findBundleFiles(resourceRoot, component, relativeFile) {
  const componentRoot = path.join(resourceRoot, "assets", component);
  if (!fs.existsSync(componentRoot)) {
    throw new Error(`Missing EDA component directory: ${componentRoot}`);
  }
  const files = fs
    .readdirSync(componentRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => path.join(componentRoot, entry.name, relativeFile))
    .filter((file) => fs.existsSync(file))
    .sort();
  if (files.length === 0) {
    throw new Error(
      `Cannot find ${relativeFile} in any installed ${component} version`,
    );
  }
  return files;
}

function countLiteral(source, marker) {
  let count = 0;
  let offset = 0;
  while ((offset = source.indexOf(marker, offset)) >= 0) {
    count += 1;
    offset += marker.length;
  }
  return count;
}

function replaceLiteralOnce(source, marker, replacement, label) {
  const count = countLiteral(source, marker);
  if (count !== 1) {
    throw new Error(`${label}: expected one marker, found ${count}`);
  }
  return source.replace(marker, replacement);
}

function matchRegexOnce(source, regex, label) {
  const flags = regex.flags.replace("g", "");
  const matcher = new RegExp(regex.source, flags);
  const first = matcher.exec(source);
  if (!first) {
    throw new Error(`${label}: patch marker was not found`);
  }
  const tail = source.slice(first.index + first[0].length);
  if (matcher.test(tail)) {
    throw new Error(`${label}: patch marker is not unique`);
  }
  return first;
}

function replaceRegexOnce(source, regex, replacer, label) {
  const match = matchRegexOnce(source, regex, label);
  const replacement =
    typeof replacer === "function" ? replacer(match) : replacer;
  return (
    source.slice(0, match.index) +
    replacement +
    source.slice(match.index + match[0].length)
  );
}

function parseJavaScript(source, file) {
  try {
    new vm.Script(source, { filename: file });
  } catch (error) {
    throw new Error(`${file}: patched JavaScript does not parse: ${error}`);
  }
}

function assertIncludes(source, markers, label) {
  for (const marker of markers) {
    if (!source.includes(marker)) {
      throw new Error(`${label}: verification marker is missing: ${marker}`);
    }
  }
}

function patchPcbEngine(source, file) {
  const fullyPatched =
    source.includes('"/engine/raytracer/getRenderConfig"') &&
    source.includes("CodexRayTracerBBox");
  if (fullyPatched) {
    return source;
  }

  const loopRendererMatches = [
    ...source.matchAll(
      /this\.loopRender=new ([$\w]+)\(this\.renderer\),this\.loopRender\.renderMode="pinhole"/g,
    ),
  ];
  const loopRendererNames = new Set(loopRendererMatches.map((match) => match[1]));
  if (loopRendererNames.size !== 1) {
    throw new Error(
      `${file}: cannot identify the ray-tracer loop renderer uniquely`,
    );
  }
  const loopRendererName = [...loopRendererNames][0];

  const initRegex =
    /async initRayTracer\(([$\w]+),([$\w]+)\)\{let ([$\w]+)=await ([$\w]+)\.build1\(this\.gpu,this\.currentCamera\);await \3\.buildByKitsune\(\{obj:\{mtl:\1,obj:\2,origin:this\.rulerProgram\.getOrigin\(\)\},pcb:\{planeGPU:this\.planes,staticPolygonInfoBuilder:this\.staticPolygonInfoBuilder\}\},this\.context\),([$\w]+)\.downloadFile\("raytracer\.zip",await \3\.getZip\(\)\),this\.rayTracing=\3\}/;

  source = replaceRegexOnce(
    source,
    initRegex,
    (match) => {
      const [materialArg, objectArg, localRayTracer, rayTracerClass] = [
        match[1],
        match[2],
        match[3],
        match[4],
      ];
      return (
        `async initRayTracer(${materialArg},${objectArg}){` +
        "if(this.rayTracing)return!1;" +
        `if(!${materialArg}||!${objectArg}){` +
        "let CodexRayTracerBBox=this.getBBox3()," +
        "CodexRayTracerMinX=CodexRayTracerBBox&&Number.isFinite(CodexRayTracerBBox.minX)?CodexRayTracerBBox.minX:-1," +
        "CodexRayTracerMinY=CodexRayTracerBBox&&Number.isFinite(CodexRayTracerBBox.minY)?CodexRayTracerBBox.minY:-1," +
        "CodexRayTracerMaxX=CodexRayTracerBBox&&Number.isFinite(CodexRayTracerBBox.maxX)?CodexRayTracerBBox.maxX:1," +
        "CodexRayTracerMaxY=CodexRayTracerBBox&&Number.isFinite(CodexRayTracerBBox.maxY)?CodexRayTracerBBox.maxY:1;" +
        `${materialArg}=["newmtl __eda_raytracer_placeholder","Ka 0 0 0","Kd 0 0 0","Ks 0 0 0","endmtl"].join("\\n"),` +
        `${objectArg}=["o __eda_raytracer_placeholder","v "+CodexRayTracerMinX+" "+CodexRayTracerMinY+" 0","v "+CodexRayTracerMaxX+" "+CodexRayTracerMinY+" 0","v "+CodexRayTracerMaxX+" "+CodexRayTracerMaxY+" 0","v "+CodexRayTracerMinX+" "+CodexRayTracerMaxY+" 0","vn 0 0 1","usemtl __eda_raytracer_placeholder","f 1//1 2//1 3//1","f 1//1 3//1 4//1"].join("\\n")` +
        "}" +
        `let ${localRayTracer}=await ${rayTracerClass}.build1(this.gpu,this.currentCamera);` +
        `await ${localRayTracer}.buildByKitsune({obj:{mtl:${materialArg},obj:${objectArg},origin:this.rulerProgram.getOrigin()},pcb:{planeGPU:this.planes,staticPolygonInfoBuilder:this.staticPolygonInfoBuilder}},this.context),` +
        `${localRayTracer}.loopRender=new ${loopRendererName}(${localRayTracer}.renderer),` +
        `${localRayTracer}.loopRender.renderMode="pinhole",` +
        `${localRayTracer}.setGlobalParam({hideOBJ:!0}),` +
        `this.rayTracing=${localRayTracer},this.needRender=!0,!0}`
      );
    },
    `${file}: ray-tracer initialization`,
  );

  const serviceRegex =
    /([\w$]+)\.rpcService\("\/engine\/scene\/getRulerTextColor",\(\)=>this\.getRulerStringColor\(\)\)\}setFpsLogTime/;
  source = replaceRegexOnce(
    source,
    serviceRegex,
    (match) => {
      const bus = match[1];
      return (
        `${match[0].slice(0, -"}setFpsLogTime".length)},` +
        `${bus}.rpcService("/engine/raytracer/init",async()=>this.initRayTracer()),` +
        `${bus}.rpcService("/engine/raytracer/dispose",()=>{let CodexRayTracerWasActive=!!this.rayTracing;return this.rayTracing=void 0,this.needRender=!0,CodexRayTracerWasActive}),` +
        `${bus}.rpcService("/engine/raytracer/setRenderConfig",CodexRayTracerConfig=>{if(!this.rayTracing)throw new Error("Ray tracer is not initialized");let CodexRayTracerCurrent=this.rayTracing.getGlobalParam(),CodexRayTracerNext={...(CodexRayTracerConfig||{})};for(let CodexRayTracerKey of["backgroundColor","occluderColor","occluderPosition"]){let CodexRayTracerValue=CodexRayTracerNext[CodexRayTracerKey],CodexRayTracerTemplate=CodexRayTracerCurrent[CodexRayTracerKey];CodexRayTracerValue&&typeof CodexRayTracerValue=="object"&&CodexRayTracerTemplate&&(CodexRayTracerNext[CodexRayTracerKey]=Object.assign(Object.create(Object.getPrototypeOf(CodexRayTracerTemplate)),CodexRayTracerValue))}this.rayTracing.setGlobalParam(CodexRayTracerNext),this.needRender=!0}),` +
        `${bus}.rpcService("/engine/raytracer/getRenderConfig",()=>{if(!this.rayTracing)throw new Error("Ray tracer is not initialized");return JSON.parse(JSON.stringify(this.rayTracing.getGlobalParam()))}),` +
        `${bus}.rpcService("/engine/raytracer/getLightConfig",CodexRayTracerLightName=>{if(!this.rayTracing)throw new Error("Ray tracer is not initialized");let CodexRayTracerLight=this.rayTracing.getLight().get(CodexRayTracerLightName);return CodexRayTracerLight?JSON.parse(JSON.stringify(CodexRayTracerLight)):void 0}),` +
        `${bus}.rpcService("/engine/raytracer/hitMaterial",async CodexRayTracerPoint=>{if(!this.rayTracing)return null;let CodexRayTracerHit=await this.rayTracing.gitRayHitInfo(CodexRayTracerPoint[0],CodexRayTracerPoint[1]);return CodexRayTracerHit?JSON.parse(JSON.stringify(CodexRayTracerHit)):null}),` +
        `${bus}.rpcService("/engine/raytracer/getCameraConfig",()=>{if(!this.rayTracing)return null;let CodexRayTracerCamera=this.currentCamera,CodexRayTracerPosition=CodexRayTracerCamera.getPosition(),CodexRayTracerDirection=CodexRayTracerCamera.getTar2Pos().normalize(),CodexRayTracerUp=CodexRayTracerCamera.getUp().normalize(),CodexRayTracerDegrees=180/Math.PI;return{position:{x:CodexRayTracerPosition.x,y:CodexRayTracerPosition.y,z:CodexRayTracerPosition.z},rotation:{x:Math.atan2(CodexRayTracerDirection.x,-CodexRayTracerDirection.y)*CodexRayTracerDegrees,y:Math.asin(Math.max(-1,Math.min(1,CodexRayTracerDirection.z)))*CodexRayTracerDegrees,z:Math.atan2(CodexRayTracerUp.x,CodexRayTracerUp.z)*CodexRayTracerDegrees},focalLength:Number(CodexRayTracerCamera.getFocalLength()||0)}})` +
        "}setFpsLogTime"
      );
    },
    `${file}: ray-tracer engine services`,
  );

  assertIncludes(
    source,
    [
      '"/engine/raytracer/init"',
      '"/engine/raytracer/dispose"',
      '"/engine/raytracer/setRenderConfig"',
      '"/engine/raytracer/getRenderConfig"',
      '"/engine/raytracer/getLightConfig"',
      '"/engine/raytracer/hitMaterial"',
      '"/engine/raytracer/getCameraConfig"',
      "CodexRayTracerBBox",
    ],
    file,
  );
  return source;
}

function patchPcb3dController(source, file) {
  if (source.includes("CodexRayTracerControllerV2")) {
    return source;
  }

  const hiddenInitRegex =
    /\/\\braytracer\\b\/\.test\(([$\w]+)\.location\.search\)&&await ([$\w]+)\.rpcCall\("(?:\/engine\/initRayTracer|\/engine\/raytracer\/init)"\)/;
  const hiddenInit = matchRegexOnce(
    source,
    hiddenInitRegex,
    `${file}: unfinished ray-tracer entry`,
  );
  const topWindow = hiddenInit[1];
  const bus = hiddenInit[2];

  const uiBusMatch = matchRegexOnce(
    source,
    /([\w$]+)\.publish\("\/pcb\/3d\/changeInfo",/,
    `${file}: parent UI message bus`,
  );
  const uiBus = uiBusMatch[1];

  const canvasMatch = matchRegexOnce(
    source,
    /let ([$\w]+)=([$\w]+)\.style\.cursor,([$\w]+)=/,
    `${file}: 3D canvas`,
  );
  const canvas = canvasMatch[2];

  const viewStateMatch = matchRegexOnce(
    source,
    /rpcService\("\/pcb\/3d\/sync\/3dview",async ([$\w]+)=>\{[\s\S]{0,300}?\[([$\w]+)\.tabid,\2\.pcbUuid\]=\1/,
    `${file}: 3D view state`,
  );
  const viewState = viewStateMatch[2];

  const controller =
    "(()=>{let CodexRayTracerControllerV2=globalThis.__CodexRayTracerControllerV2||(globalThis.__CodexRayTracerControllerV2={active:!1,pointerDown:null,cameraTimer:void 0,installed:!1});" +
    "if(!CodexRayTracerControllerV2.installed){CodexRayTracerControllerV2.installed=!0," +
    `${bus}.rpcService("/pcb/3d/raytracer/init",async()=>{let CodexRayTracerResult=(await ${bus}.rpcCall("/engine/raytracer/init")).message;return CodexRayTracerControllerV2.active=!0,CodexRayTracerResult}),` +
    `${bus}.rpcService("/pcb/3d/raytracer/dispose",async()=>{CodexRayTracerControllerV2.active=!1,clearTimeout(CodexRayTracerControllerV2.cameraTimer);return(await ${bus}.rpcCall("/engine/raytracer/dispose")).message}),` +
    `${bus}.rpcService("/pcb/3d/raytracer/setRenderConfig",async CodexRayTracerConfig=>(await ${bus}.rpcCall("/engine/raytracer/setRenderConfig",CodexRayTracerConfig)).message),` +
    `${bus}.rpcService("/pcb/3d/raytracer/getRenderConfig",async()=>(await ${bus}.rpcCall("/engine/raytracer/getRenderConfig")).message),` +
    `${bus}.rpcService("/pcb/3d/raytracer/getLightConfig",async CodexRayTracerLightName=>(await ${bus}.rpcCall("/engine/raytracer/getLightConfig",CodexRayTracerLightName)).message),` +
    `${bus}.subscribe("/engine/camera/update",()=>{CodexRayTracerControllerV2.active&&(clearTimeout(CodexRayTracerControllerV2.cameraTimer),CodexRayTracerControllerV2.cameraTimer=setTimeout(async()=>{try{let CodexRayTracerCamera=(await ${bus}.rpcCall("/engine/raytracer/getCameraConfig")).message;CodexRayTracerCamera&&${uiBus}.publish("/extensionApi/PCB_RayTracerEngine/cameraChange",CodexRayTracerCamera,${topWindow})}catch(CodexRayTracerError){console.warn("Ray tracer camera event failed",CodexRayTracerError)}},16))}),` +
    `${canvas}.addEventListener("pointerdown",CodexRayTracerEvent=>{CodexRayTracerControllerV2.active&&CodexRayTracerEvent.button===0&&(CodexRayTracerControllerV2.pointerDown={x:CodexRayTracerEvent.clientX,y:CodexRayTracerEvent.clientY})}),` +
    `${canvas}.addEventListener("pointercancel",()=>{CodexRayTracerControllerV2.pointerDown=null}),` +
    `${canvas}.addEventListener("pointerup",async CodexRayTracerEvent=>{if(!CodexRayTracerControllerV2.active||CodexRayTracerEvent.button!==0||!CodexRayTracerControllerV2.pointerDown)return;let CodexRayTracerDistance=Math.hypot(CodexRayTracerEvent.clientX-CodexRayTracerControllerV2.pointerDown.x,CodexRayTracerEvent.clientY-CodexRayTracerControllerV2.pointerDown.y);if(CodexRayTracerControllerV2.pointerDown=null,CodexRayTracerDistance>3)return;let CodexRayTracerRect=${canvas}.getBoundingClientRect(),CodexRayTracerX=(CodexRayTracerEvent.clientX-CodexRayTracerRect.left)*${canvas}.width/CodexRayTracerRect.width,CodexRayTracerY=(CodexRayTracerEvent.clientY-CodexRayTracerRect.top)*${canvas}.height/CodexRayTracerRect.height;try{let CodexRayTracerHit=(await ${bus}.rpcCall("/engine/raytracer/hitMaterial",[CodexRayTracerX,CodexRayTracerY])).message;CodexRayTracerHit&&${uiBus}.publish("/extensionApi/PCB_RayTracerEngine/clickMaterial",{materialId:CodexRayTracerHit.materialId,material:CodexRayTracerHit.material},${topWindow})}catch(CodexRayTracerError){console.warn("Ray tracer material event failed",CodexRayTracerError)}})` +
    `}${uiBus}.publish("/extensionApi/PCB_RayTracerEngine/ready",${viewState}.tabid,${topWindow})})()`;

  const replacement =
    `${controller},/\\braytracer\\b/.test(${topWindow}.location.search)&&await ${bus}.rpcCall("/pcb/3d/raytracer/init")`;
  if (source.includes("CodexRayTracerControllerActive")) {
    const oldControllerStart = source.indexOf(
      "(()=>{let CodexRayTracerControllerActive",
    );
    if (oldControllerStart < 0 || hiddenInit.index <= oldControllerStart) {
      throw new Error(`${file}: cannot upgrade the existing ray-tracer controller`);
    }
    source =
      source.slice(0, oldControllerStart) +
      replacement +
      source.slice(hiddenInit.index + hiddenInit[0].length);
  } else {
    source = replaceRegexOnce(
      source,
      hiddenInitRegex,
      replacement,
      `${file}: ray-tracer controller and events`,
    );
  }

  assertIncludes(
    source,
    [
      "CodexRayTracerControllerV2",
      '"/pcb/3d/raytracer/init"',
      '"/extensionApi/PCB_RayTracerEngine/ready"',
      '"/extensionApi/PCB_RayTracerEngine/clickMaterial"',
      '"/extensionApi/PCB_RayTracerEngine/cameraChange"',
      '"/engine/raytracer/init"',
    ],
    file,
  );
  return source;
}

function extractUiIdentifiers(source, file) {
  const pcbPredicate = matchRegexOnce(
    source,
    /function ([$\w]+)\(\)\{let ([$\w]+)=([$\w]+)\.getActiveTabData\(\);return\(\2\.data\.doctype\|\|\2\.data\.docType\)===([$\w]+)\.PCB\|\|/,
    `${file}: PCB document predicate`,
  );
  const tabManager = pcbPredicate[3];
  const docType = pcbPredicate[4];

  const commandSubscription = matchRegexOnce(
    source,
    /([$\w]+)\.messageBus\.subscribe\("Pcb\/doCommand",([$\w]+)=>\{typeof \2=="string"\?([$\w]+)\(\2\):\3\(\2\.cmd,\2\.args\)\}\)/,
    `${file}: PCB command dispatcher`,
  );
  return {
    globalState: commandSubscription[1],
    command: commandSubscription[3],
    tabManager,
    docType,
  };
}

function patchUiRayTracer(source, file) {
  if (source.includes("CodexRayTracerBridgeV2=1")) {
    return source;
  }
  const { globalState, command, tabManager, docType } = extractUiIdentifiers(
    source,
    file,
  );
  const routeMap = matchRegexOnce(
    source,
    /var ([$\w]+)=\{"-extensionApi":\{/,
    `${file}: extension API route map`,
  );

  const bridge =
    "var CodexRayTracerBridgeV2=1,CodexRayTracerTabId,CodexRayTracerReadyTabs=new Set,CodexRayTracerReadyWaiters=new Map;" +
    "var CodexRayTracerBridge=class{" +
    `static markReady(CodexRayTracerTarget){if(!CodexRayTracerTarget)return;CodexRayTracerReadyTabs.add(CodexRayTracerTarget);let CodexRayTracerWaiters=CodexRayTracerReadyWaiters.get(CodexRayTracerTarget)||[];CodexRayTracerReadyWaiters.delete(CodexRayTracerTarget),CodexRayTracerWaiters.forEach(CodexRayTracerResolve=>CodexRayTracerResolve())}` +
    `static async waitReady(CodexRayTracerTarget){if(CodexRayTracerReadyTabs.has(CodexRayTracerTarget))return;await new Promise((CodexRayTracerResolve,CodexRayTracerReject)=>{let CodexRayTracerWaiters=CodexRayTracerReadyWaiters.get(CodexRayTracerTarget)||[],CodexRayTracerTimer=setTimeout(()=>{let CodexRayTracerPending=CodexRayTracerReadyWaiters.get(CodexRayTracerTarget)||[];CodexRayTracerReadyWaiters.set(CodexRayTracerTarget,CodexRayTracerPending.filter(CodexRayTracerEntry=>CodexRayTracerEntry!==CodexRayTracerDone)),CodexRayTracerReject(new Error("Timed out waiting for the PCB 3D preview"))},120*1e3),CodexRayTracerDone=()=>{clearTimeout(CodexRayTracerTimer),CodexRayTracerResolve()};CodexRayTracerWaiters.push(CodexRayTracerDone),CodexRayTracerReadyWaiters.set(CodexRayTracerTarget,CodexRayTracerWaiters)})}` +
    `static async resolve(CodexRayTracerInitialize=!1){let CodexRayTracerActive=${tabManager}.getActiveTab(),CodexRayTracerType=${tabManager}.getTabDocType(CodexRayTracerActive),CodexRayTracerTarget;if(CodexRayTracerType===${docType}.PCB||CodexRayTracerType===${docType}.FOOTPRINT)CodexRayTracerInitialize?(await ${command}("Preview3D"),CodexRayTracerTarget=${tabManager}.getActiveTab()):CodexRayTracerTarget=CodexRayTracerTabId;else CodexRayTracerType===${docType}.VIEW3D?CodexRayTracerTarget=CodexRayTracerActive:CodexRayTracerTarget=CodexRayTracerTabId;if(!CodexRayTracerTarget)throw new Error("Please open a PCB, footprint, or PCB 3D preview");CodexRayTracerInitialize&&await this.waitReady(CodexRayTracerTarget);let CodexRayTracerFrame=await ${tabManager}.getTabIFrame(CodexRayTracerTarget);if(!CodexRayTracerFrame||!CodexRayTracerFrame.contentWindow)throw new Error("PCB 3D preview is not available");return CodexRayTracerTabId=CodexRayTracerTarget,CodexRayTracerFrame.contentWindow}` +
    `static async call(CodexRayTracerRoute,CodexRayTracerData,CodexRayTracerInitialize=!1){let CodexRayTracerWindow=await this.resolve(CodexRayTracerInitialize);return(await ${globalState}.windowBridge.rpcCall(CodexRayTracerRoute,CodexRayTracerData,CodexRayTracerWindow,120*1e3)).message}` +
    'static async init(CodexRayTracerExtensionUuid){return this.call("/pcb/3d/raytracer/init",CodexRayTracerExtensionUuid,!0)}' +
    'static async dispose(){return this.call("/pcb/3d/raytracer/dispose")}' +
    'static async setRenderConfig(CodexRayTracerConfig){return this.call("/pcb/3d/raytracer/setRenderConfig",CodexRayTracerConfig)}' +
    'static async getRenderConfig(){return this.call("/pcb/3d/raytracer/getRenderConfig")}' +
    'static async getLightConfig(CodexRayTracerLightName){return this.call("/pcb/3d/raytracer/getLightConfig",CodexRayTracerLightName)}' +
    "};";

  const upgradingV1 = source.includes("var CodexRayTracerBridge=class");
  if (upgradingV1) {
    source = replaceRegexOnce(
      source,
      /var CodexRayTracerTabId;var CodexRayTracerBridge=class\{[\s\S]*?\};(?=var [$\w]+=\{"-extensionApi":\{)/,
      bridge,
      `${file}: upgrade public ray-tracer bridge`,
    );
  } else {
    source =
      source.slice(0, routeMap.index) +
      bridge +
      source.slice(routeMap.index);
  }

  if (!source.includes("PCB_RayTracerEngine:{init:CodexRayTracerBridge.init")) {
    source = replaceLiteralOnce(
      source,
      "PCB_ManufactureData:{",
      "PCB_RayTracerEngine:{init:CodexRayTracerBridge.init,dispose:CodexRayTracerBridge.dispose,setRenderConfig:CodexRayTracerBridge.setRenderConfig,getRenderConfig:CodexRayTracerBridge.getRenderConfig,getLightConfig:CodexRayTracerBridge.getLightConfig},PCB_ManufactureData:{",
      `${file}: public ray-tracer route map`,
    );
  }

  const readyEventBridge =
    `${globalState}.messageBus.subscribe("/extensionApi/PCB_RayTracerEngine/ready",CodexRayTracerTab=>{CodexRayTracerBridge.markReady(CodexRayTracerTab)}),`;
  const clickEventMarker = `${globalState}.messageBus.subscribe("/extensionApi/PCB_RayTracerEngine/clickMaterial",`;
  if (source.includes(clickEventMarker)) {
    source = replaceLiteralOnce(
      source,
      clickEventMarker,
      readyEventBridge + clickEventMarker,
      `${file}: ray-tracer ready event bridge`,
    );
  } else {
    const eventMarker = `${globalState}.messageBus.subscribe("leftTree-net",`;
    const eventBridge =
    readyEventBridge +
    `${globalState}.messageBus.subscribe("/extensionApi/PCB_RayTracerEngine/clickMaterial",CodexRayTracerEvent=>{${globalState}.extensionApiMessageBus2.publish("extensionApi.PCB_Event.rayTracerEngine3DViewClickMaterialEvent",structuredClone(CodexRayTracerEvent))}),` +
    `${globalState}.messageBus.subscribe("/extensionApi/PCB_RayTracerEngine/cameraChange",CodexRayTracerEvent=>{${globalState}.extensionApiMessageBus2.publish("extensionApi.PCB_Event.rayTracerEngine3DViewCameraChangeEvent",structuredClone(CodexRayTracerEvent))}),` +
    eventMarker;
    source = replaceLiteralOnce(
      source,
      eventMarker,
      eventBridge,
      `${file}: ray-tracer event bridge`,
    );
  }

  assertIncludes(
    source,
    [
      "CodexRayTracerBridgeV2=1",
      "var CodexRayTracerBridge=class",
      '"/extensionApi/PCB_RayTracerEngine/ready"',
      "PCB_RayTracerEngine:{init:CodexRayTracerBridge.init",
      "extensionApi.PCB_Event.rayTracerEngine3DViewClickMaterialEvent",
      "extensionApi.PCB_Event.rayTracerEngine3DViewCameraChangeEvent",
    ],
    file,
  );
  return source;
}

function patchUiCreateNetLabel(source, file) {
  if (source.includes("CodexNetLabelBridgeV2")) {
    return source;
  }

  const existingBridgeRegex =
    /static async createNetLabel\(([$\w]+)\)\{return\(await ([$\w]+)\.messageBus\.rpcCall\("extensionApi\/SCH_PrimitiveAttribute_createNetLabel",\1\)\)\.message\}/;
  const existingBridge = new RegExp(existingBridgeRegex.source).exec(source);
  if (existingBridge) {
    const argument = existingBridge[1];
    const globalState = existingBridge[2];
    return replaceRegexOnce(
      source,
      existingBridgeRegex,
      `static async createNetLabel(${argument}){let CodexNetLabelBridgeV2=(await ${globalState}.messageBus.rpcCall("extensionApi/SCH_PrimitiveAttribute_createNetLabel",${argument})).message;if(CodexNetLabelBridgeV2&&typeof CodexNetLabelBridgeV2=="object"&&CodexNetLabelBridgeV2.__CodexNetLabelError)throw new Error(CodexNetLabelBridgeV2.__CodexNetLabelError);return CodexNetLabelBridgeV2}`,
      `${file}: existing schematic net-label UI bridge`,
    );
  }

  const classRegex =
    /var ([$\w]+)=class\{static async get\(([$\w]+)\)\{return\(await ([$\w]+)\.messageBus\.rpcCall\("extensionApi\/SCH_PrimitiveAttribute_get",\2\)\)\.message\}static async getAllPrimitiveId\(([$\w]+)\)\{return\(await \3\.messageBus\.rpcCall\("extensionApi\/SCH_PrimitiveAttribute_getAllPrimitiveId",\4\)\)\.message\}static async getAll\(([$\w]+)\)\{return \5\?\(await \3\.messageBus\.rpcCall\("extensionApi\/SCH_PrimitiveAttribute_getAll",\5\)\)\.message:\[\]\}static async modify\(/;
  const classMatch = matchRegexOnce(
    source,
    classRegex,
    `${file}: schematic attribute bridge`,
  );
  const attributeClass = classMatch[1];
  const globalState = classMatch[3];
  const argument = classMatch[5];
  source = replaceRegexOnce(
    source,
    classRegex,
    (match) =>
      `${match[0].slice(0, -"static async modify(".length)}` +
      `static async createNetLabel(${argument}){let CodexNetLabelBridgeV2=(await ${globalState}.messageBus.rpcCall("extensionApi/SCH_PrimitiveAttribute_createNetLabel",${argument})).message;if(CodexNetLabelBridgeV2&&typeof CodexNetLabelBridgeV2=="object"&&CodexNetLabelBridgeV2.__CodexNetLabelError)throw new Error(CodexNetLabelBridgeV2.__CodexNetLabelError);return CodexNetLabelBridgeV2}` +
      "static async modify(",
    `${file}: schematic net-label UI bridge`,
  );

  const routeMarker = `SCH_PrimitiveAttribute:{get:${attributeClass}.get,getAllPrimitiveId:${attributeClass}.getAllPrimitiveId,getAll:${attributeClass}.getAll,modify:${attributeClass}.modify}`;
  const routeReplacement = `SCH_PrimitiveAttribute:{get:${attributeClass}.get,getAllPrimitiveId:${attributeClass}.getAllPrimitiveId,getAll:${attributeClass}.getAll,createNetLabel:${attributeClass}.createNetLabel,modify:${attributeClass}.modify}`;
  return replaceLiteralOnce(
    source,
    routeMarker,
    routeReplacement,
    `${file}: schematic net-label public route`,
  );
}

function patchSchCreateNetLabel(source, file) {
  if (source.includes("CodexNetLabelNativeV2")) {
    return source;
  }

  if (!source.includes("canvas.placeNetLabel.switchTool()")) {
    throw new Error(`${file}: the native net-label placement tool was not found`);
  }

  const modifyRoute = matchRegexOnce(
    source,
    /,"-extensionApi\/SCH_PrimitiveAttribute_modify":async ([$\w]+)=>/,
    `${file}: schematic attribute modification route`,
  );
  const inputArgument = modifyRoute[1];

  const getRouteStart = source.indexOf(
    '"-extensionApi/SCH_PrimitiveAttribute_get":',
  );
  const getRouteEnd = source.indexOf(
    '"-extensionApi/SCH_PrimitiveAttribute_getAllPrimitiveId":',
    getRouteStart,
  );
  if (getRouteStart < 0 || getRouteEnd <= getRouteStart) {
    throw new Error(`${file}: cannot locate the schematic attribute getter`);
  }
  const getRoute = source.slice(getRouteStart, getRouteEnd);
  const documentManagerMatch = matchRegexOnce(
    getRoute,
    /([\w$]+)\.instance\.getActiveDoc\(\)/,
    `${file}: schematic document manager`,
  );
  const serializerMatch = matchRegexOnce(
    getRoute,
    /\.map\(([$\w]+)=>([$\w]+)\(\1\)\)/,
    `${file}: net-label API serializer`,
  );
  const documentManager = documentManagerMatch[1];
  const serializer = serializerMatch[2];

  const getAllIdRouteEnd = source.indexOf(
    '"-extensionApi/SCH_PrimitiveAttribute_getAll":',
    getRouteEnd,
  );
  if (getAllIdRouteEnd <= getRouteEnd) {
    throw new Error(`${file}: cannot locate the schematic attribute ID getter`);
  }
  const getAllIdRoute = source.slice(getRouteEnd, getAllIdRouteEnd);
  const attributeTypesMatch = matchRegexOnce(
    getAllIdRoute,
    /instanceof ([$\w]+)\|\|[$\w]+ instanceof ([$\w]+)/,
    `${file}: schematic attribute model types`,
  );
  const attributeTypeA = attributeTypesMatch[1];
  const attributeTypeB = attributeTypesMatch[2];

  function getUniqueIdentifier(regex, captureIndex, label) {
    const matches = [...source.matchAll(regex)];
    const identifiers = new Set(matches.map((match) => match[captureIndex]));
    if (identifiers.size !== 1) {
      throw new Error(
        `${file}: cannot identify ${label} uniquely (found ${identifiers.size})`,
      );
    }
    return [...identifiers][0];
  }

  const actionContext = getUniqueIdentifier(
    /([$\w]+)\.actionRunner\.tryWaitRealTimeSyncActionEnd\(\)/g,
    1,
    "the action context",
  );
  const actionGuard = getUniqueIdentifier(
    /([$\w]+)\.checkOtherActionRunning\(\)/g,
    1,
    "the action guard",
  );
  const pointMatch = matchRegexOnce(
    source,
    /get\[Symbol\.toStringTag\]\(\)\{return"Vector2"\}\};([$\w]+)\.ORIGIN=new \1\(0,0\);var ([$\w]+)=\1;/,
    `${file}: schematic point class`,
  );
  const pointClass = pointMatch[2];

  const replacement =
    `,"-extensionApi/SCH_PrimitiveAttribute_createNetLabel":async ${inputArgument}=>{` +
    'let CodexNetLabelNativeV2=1,CodexNetLabelDoc,CodexNetLabelTool,CodexNetLabelStarted=!1;' +
    'try{' +
    `let{x:CodexNetLabelX,y:CodexNetLabelY,net:CodexNetLabelNet}=${inputArgument}||{};CodexNetLabelDoc=${documentManager}.instance.getActiveDoc();` +
    'if(!CodexNetLabelDoc||!CodexNetLabelDoc.canvas||!CodexNetLabelDoc.isSchSheetDoc())throw new Error("Please open a schematic page");' +
    'if(!Number.isFinite(CodexNetLabelX)||!Number.isFinite(CodexNetLabelY))throw new Error("Invalid net label coordinates");' +
    'if(typeof CodexNetLabelNet!="string"||!CodexNetLabelNet.length)throw new Error("Net name cannot be empty");' +
    'if(CodexNetLabelDoc.shapeManager.getDrawPlaceDisableByModelTagName("NetLabel"))throw new Error("Net label placement is disabled");' +
    `await ${actionContext}.actionRunner.tryWaitRealTimeSyncActionEnd();` +
    `if(${actionGuard}.checkOtherActionRunning())throw new Error("Another action is running");` +
    'for(let CodexNetLabelCanvasAction of CodexNetLabelDoc.canvas.eventReactor.actions)await CodexNetLabelCanvasAction.tryCancelOrAtLastPointComplete();' +
    'let CodexNetLabelBefore=new Set;CodexNetLabelDoc.shapeManager.idManager.idMap.forEach((CodexNetLabelValue,CodexNetLabelId)=>{(CodexNetLabelValue instanceof ' +
    attributeTypeA +
    '||CodexNetLabelValue instanceof ' +
    attributeTypeB +
    ')&&CodexNetLabelBefore.add(CodexNetLabelId)});' +
    `let CodexNetLabelPoint=new ${pointClass}(CodexNetLabelX,-CodexNetLabelY);` +
    'CodexNetLabelTool=CodexNetLabelDoc.canvas.placeNetLabel,CodexNetLabelTool.start(),CodexNetLabelStarted=!0;' +
    'let CodexNetLabelModel=CodexNetLabelTool.model;if(!CodexNetLabelModel)throw new Error("Native net-label tool did not create a model");' +
    'CodexNetLabelModel.value=CodexNetLabelNet,CodexNetLabelModel.translateToXY(CodexNetLabelPoint.x,CodexNetLabelPoint.y);' +
    'if(!await CodexNetLabelTool.verify(CodexNetLabelPoint))throw new Error("Native net-label placement verification failed");' +
    'await CodexNetLabelTool.end(),CodexNetLabelStarted=!!CodexNetLabelTool.action.isUnderway,CodexNetLabelDoc.canvas.cmd=null;' +
    'if(CodexNetLabelStarted)throw new Error("Native net-label action did not finish");' +
    'let CodexNetLabelResult=CodexNetLabelDoc.shapeManager.idManager.get(CodexNetLabelModel.id);' +
    'if(!(CodexNetLabelResult instanceof ' +
    attributeTypeA +
    ')&&!(CodexNetLabelResult instanceof ' +
    attributeTypeB +
    ')){let CodexNetLabelBestScore=1/0;CodexNetLabelResult=void 0;CodexNetLabelDoc.shapeManager.idManager.idMap.forEach(CodexNetLabelCandidate=>{if((CodexNetLabelCandidate instanceof ' +
    attributeTypeA +
    '||CodexNetLabelCandidate instanceof ' +
    attributeTypeB +
    ')&&CodexNetLabelCandidate.parent&&CodexNetLabelCandidate.value===CodexNetLabelNet){let CodexNetLabelDX=Number(CodexNetLabelCandidate.x)-CodexNetLabelPoint.x,CodexNetLabelDY=Number(CodexNetLabelCandidate.y)-CodexNetLabelPoint.y,CodexNetLabelScore=(CodexNetLabelBefore.has(CodexNetLabelCandidate.id)?1e12:0)+CodexNetLabelDX*CodexNetLabelDX+CodexNetLabelDY*CodexNetLabelDY;CodexNetLabelScore<CodexNetLabelBestScore&&(CodexNetLabelBestScore=CodexNetLabelScore,CodexNetLabelResult=CodexNetLabelCandidate)}})}' +
    'if(!CodexNetLabelResult||!CodexNetLabelResult.parent)throw new Error("Native placement ended without a net-label attribute");' +
    `return ${serializer}(CodexNetLabelResult)` +
    '}catch(CodexNetLabelError){if(CodexNetLabelStarted&&CodexNetLabelTool)try{CodexNetLabelTool.reset()}catch(CodexNetLabelCleanupError){}CodexNetLabelDoc&&CodexNetLabelDoc.canvas&&(CodexNetLabelDoc.canvas.cmd=null);return{__CodexNetLabelError:CodexNetLabelError&&CodexNetLabelError.message||String(CodexNetLabelError)}}}';

  const existingRouteStart = source.indexOf(
    ',"-extensionApi/SCH_PrimitiveAttribute_createNetLabel":',
  );
  if (existingRouteStart >= 0) {
    if (existingRouteStart >= modifyRoute.index) {
      throw new Error(`${file}: malformed schematic net-label route order`);
    }
    return (
      source.slice(0, existingRouteStart) +
      replacement +
      source.slice(modifyRoute.index)
    );
  }
  return source.slice(0, modifyRoute.index) + replacement + source.slice(modifyRoute.index);
}

function verifyApiFacade(source, file) {
  assertIncludes(
    source,
    [
      "extensionApi.PCB_RayTracerEngine.init",
      "extensionApi.PCB_RayTracerEngine.dispose",
      "extensionApi.PCB_RayTracerEngine.setRenderConfig",
      "extensionApi.PCB_RayTracerEngine.getRenderConfig",
      "extensionApi.PCB_RayTracerEngine.getLightConfig",
      "extensionApi.PCB_Event.rayTracerEngine3DViewClickMaterialEvent",
      "extensionApi.PCB_Event.rayTracerEngine3DViewCameraChangeEvent",
      "extensionApi.SCH_PrimitiveAttribute.createNetLabel",
    ],
    file,
  );
}

const resourceRoot = findResourceRoot(appRoot);
const packageJson = JSON.parse(
  fs.readFileSync(path.join(resourceRoot, "package.json"), "utf8"),
);
const appVersion = packageJson.version || "unknown-version";
const backupRoot = path.join(
  workspaceRoot,
  ".codex-backups",
  "eda-allapi",
  `${appVersion}-${shortPathHash(appRoot)}`,
);

const uiFiles = findBundleFiles(resourceRoot, "pro-ui", "js/ui.js");
const pcbEngineFiles = findBundleFiles(resourceRoot, "pro-pcb", "js/pcb.js");
const pcb3dFiles = findBundleFiles(resourceRoot, "pro-pcb", "js/pcb3d.js");
const schFiles = findBundleFiles(resourceRoot, "pro-sch", "js/sch-main.js");
const apiFiles = findBundleFiles(resourceRoot, "pro-api", "api.js");

for (const apiFile of apiFiles) {
  verifyApiFacade(fs.readFileSync(apiFile, "utf8"), apiFile);
}

const pending = [];
function stage(file, transform) {
  const original = fs.readFileSync(file, "utf8");
  const patched = transform(original, file);
  parseJavaScript(patched, file);
  pending.push({ file, original, patched });
}

for (const file of pcbEngineFiles) stage(file, patchPcbEngine);
for (const file of pcb3dFiles) stage(file, patchPcb3dController);
for (const file of uiFiles) {
  stage(file, (source, label) =>
    patchUiCreateNetLabel(patchUiRayTracer(source, label), label),
  );
}
for (const file of schFiles) stage(file, patchSchCreateNetLabel);

const results = [];
for (const item of pending) {
  const changed = item.original !== item.patched;
  const result = {
    file: item.file,
    changed,
    beforeSha256: sha256(item.original),
    sha256: sha256(item.patched),
  };
  if (changed && !dryRun) {
    const relative = path.relative(resourceRoot, item.file);
    const backupFile = path.join(backupRoot, relative + ".orig");
    fs.mkdirSync(path.dirname(backupFile), { recursive: true });
    if (!fs.existsSync(backupFile)) {
      fs.copyFileSync(item.file, backupFile, fs.constants.COPYFILE_EXCL);
    }
    const temporaryFile = `${item.file}.codex-allapi-tmp`;
    fs.writeFileSync(temporaryFile, item.patched);
    fs.renameSync(temporaryFile, item.file);
    result.backupFile = backupFile;
  }
  results.push(result);
}

console.log(
  JSON.stringify(
    {
      appRoot,
      resourceRoot,
      appVersion,
      dryRun,
      backupRoot,
      results,
    },
    null,
    2,
  ),
);
