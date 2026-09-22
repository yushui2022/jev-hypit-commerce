const assetNames = ["clip0", "clip1", "clip2", "clip3", "sheet0", "sheet1", "sheet2", "sheet3", "sheet4", "product1", "product2", "product3", "product4", "product5", "product6", "product7", "product8", "product9", "product10", "product11", "product12", "product13", "product14", "product15", "product16", "product17", "product18", "product19", "product20", "product21", "product22", "product23", "product24", "product25", "product26", "product27", "product28", "product29", "product30", "product31", "product32", "product33", "product34", "product35", "product36", "product37", "product38", "product39", "product40", "product41", "product42", "product43", "product44", "product45", "product46", "product47", "product48", "product49", "product50", "product51", "product52", "product53", "product54", "product55", "product56", "product57", "product58", "product59", "product60", "product61", "product62", "product63", "product64", "product65", "product66", "product67", "product68", "product69", "product70", "product71", "product72", "product73", "product74", "product75", "product76", "product77", "product78", "product79", "product80", "product81", "product82", "product83", "product84", "product85", "product86", "product87", "product88", "product89", "product90", "product91", "product92", "product93", "product94", "product95", "product97", "product98", "product99", "product100"];
import { assertAttributes, assertEmptyElement, canonicalize, createMarkupSurfaceHostFacet, sameType, sealGraphFragment, textAttribute } from "@hypit/hypit/author-kit";
import type { ComponentPackage, FragmentOperation, ModuleManifest, StructuredSurfaceHandler, SurfaceResolvedReference, TypeRef } from "@hypit/hypit/author-kit";
import { compositionTypes } from "@hypit/hypit/composition";
import { mediaTypes } from "@hypit/hypit/media";
import type { FontStackRef } from "@hypit/hypit/media";
import type { Timeline } from "@hypit/hypit/timeline";
import { timelineTypes } from "@hypit/hypit/timeline";
import { spatialTypes } from "@hypit/hypit/spatial";
import type { CanvasSpace } from "@hypit/hypit/spatial";
import { assertTemporalInstantFor, temporalTypes } from "@hypit/hypit/temporal";
import type { TemporalInstant, TemporalWindow } from "@hypit/hypit/temporal";
import { createTemporalInstantProjection, createTemporalWindowProjection, resolveTemporalContext,
  temporalContextAttributeVocabulary, temporalInstantAttributeNames, temporalInstantAttributeVocabulary,
  temporalWindowAttributeNames, temporalWindowAttributeVocabulary } from "@hypit/hypit/temporal-markup";
import { renderChat } from "./render.js";
import type { ChatOptions, Message } from "./render.js";

const module = { name: "@jev/matrix-ugc", version: "1" } as const;
const types = Object.fromEntries(["Options", "Message", "Messages"].map(name => [name, { module, name }])) as Record<"Options" | "Message" | "Messages", TypeRef>;
const producers = Object.fromEntries(["empty", "append", "render"].map(name => [name, { module, name }])) as Record<"empty" | "append" | "render", { module: typeof module; name: string }>;
export const manifest: ModuleManifest = { format: "hypit.module@1", ...module,
  dependencies: [mediaTypes.blobArtifact, compositionTypes.visualTrack, mediaTypes.fontStack, timelineTypes.track, spatialTypes.canvas, temporalTypes.instant].map(type => ({ module: type.module })),
  types: Object.values(types).map(type => ({ name: type.name })), capabilities: [], producers: [
    { name: "empty", inputs: [], outputs: [{ name: "messages", type: types.Messages }], needs: [] },
    { name: "append", inputs: [{ name: "messages", type: types.Messages }, { name: "message", type: types.Message },
      { name: "at", type: temporalTypes.instant }, { name: "timeline", type: timelineTypes.track }], outputs: [{ name: "messages", type: types.Messages }], needs: [] },
    { name: "render", inputs: [{ name: "messages", type: types.Messages }, { name: "options", type: types.Options },
      { name: "timeline", type: timelineTypes.track }, { name: "canvas", type: spatialTypes.canvas },
      { name: "window", type: temporalTypes.window }, { name: "font", type: mediaTypes.fontStack }, ... assetNames.map(name => ({ name, type: mediaTypes.blobArtifact }))], outputs: [{ name: "track", type: compositionTypes.visualTrack }], needs: [] },
  ],
};
const inline = <T>(record: { value: { kind: string; value?: unknown } } | undefined): T => {
  if (record?.value.kind !== "inline") throw new Error("Chat inputs must be inline values.");
  return record.value.value as T;
};
const value = (data: unknown) => ({ kind: "inline" as const, value: canonicalize(data) });
const component: ComponentPackage = { producers: [
  { producer: producers.empty, handler: () => ({ outputs: { messages: value([]) }, needs: {} }) },
  { producer: producers.append, handler: ({ inputs }) => {
    const message = inline<Omit<Message, "at">>(inputs.message), at = inline<TemporalInstant>(inputs.at);
    const messages = inline<Message[]>(inputs.messages);
    assertTemporalInstantFor(at, { subjectId: message.id, space: inline<Timeline>(inputs.timeline) });
    if (messages.some(item => item.id === message.id) || (messages.at(-1)?.at.frame ?? -1) > at.frame) throw new Error("Chat messages need unique ids and chronological arrival times.");
    return { outputs: { messages: value([...messages, { ...message, at }]) }, needs: {} };
  } },
  { producer: producers.render, handler: ({ inputs }) => ({ outputs: { track: value(renderChat(inline<Timeline>(inputs.timeline),
    inline<CanvasSpace>(inputs.canvas), inline<TemporalWindow>(inputs.window), inline<FontStackRef>(inputs.font),
    inline<Message[]>(inputs.messages), inline<ChatOptions>(inputs.options), Object.fromEntries(assetNames.map(name => [name, inputs[name]!.value as any])))) }, needs: {} }) },
] };

export const decodeSurface: StructuredSurfaceHandler = ({ element, resolveReference }) => {
  assertAttributes(element, ["id", "timeline", "canvas", "font", "title", "entrance-frames", ...assetNames, ...temporalWindowAttributeNames]);
  const id = textAttribute(element, "id"), context = resolveTemporalContext({ element, resolveReference });
  const window = createTemporalWindowProjection({ id: `${id}.window`, subjectId: id, element, ...context, resolveReference });
  const reference = (name: string, type: TypeRef): SurfaceResolvedReference => {
    const raw = element.attributes[name];
    if (typeof raw !== "object" || raw.kind !== "reference") throw new Error(`${name} must be a reference.`);
    const found = resolveReference(raw.path);
    if (found === undefined || !sameType(found.type, type)) throw new Error(`${name} has the wrong Type.`);
    return found;
  };
  const options: ChatOptions = { id, title: textAttribute(element, "title"), entranceFrames: Number(element.attributes["entrance-frames"] ?? "10") };
  const records = [...window.records, { id: `${id}.options`, type: types.Options, value: value(options), range: element.range }];
  const components = [...window.components], fragments = [...window.fragments];
  const inputs = [{ name: "timeline", type: timelineTypes.track }, { name: "canvas", type: spatialTypes.canvas },
    { name: "font", type: mediaTypes.fontStack }, { name: "window", type: temporalTypes.window }, { name: "options", type: types.Options }];
  const bindings: Record<string, SurfaceResolvedReference["ref"]> = { timeline: context.timeline.ref, canvas: reference("canvas", spatialTypes.canvas).ref,
    font: reference("font", mediaTypes.fontStack).ref, window: window.ref, options: { kind: "record", id: `${id}.options` } };
  for (const name of assetNames) { inputs.push({ name, type: mediaTypes.blobArtifact }); bindings[name] = reference(name, mediaTypes.blobArtifact).ref; }
  const input = (name: string) => ({ kind: "fragment-input" as const, name });
  const operation = (name: string) => ({ kind: "fragment-operation" as const, operation: name });
  const operations: FragmentOperation[] = [{ id: "empty", producer: producers.empty, inputs: {}, result: { kind: "output", name: "messages" } }];
  let previous = "empty", index = 0;
  for (const child of element.children) {
    if (child.kind === "text") { if (child.value.trim()) throw new Error("Chat Scene accepts Message children."); continue; }
    if (child.name.split(":").at(-1) !== "Message") throw new Error("Chat Scene accepts Message children.");
    assertAttributes(child, ["id", "sender", "text", "side", ...temporalInstantAttributeNames]); assertEmptyElement(child);
    const messageId = textAttribute(child, "id"), side = textAttribute(child, "side");
    if (side !== "left" && side !== "right") throw new Error("Message side must be left or right.");
    const at = createTemporalInstantProjection({ id: `${id}.${messageId}`, subjectId: messageId, element: child, ...context, resolveReference });
    records.push(...at.records); components.push(...at.components); fragments.push(...at.fragments);
    const key = `message-${++index}`;
    records.push({ id: `${id}.${key}`, type: types.Message, value: value({ id: messageId, sender: textAttribute(child, "sender"), text: textAttribute(child, "text"), side }), range: child.range });
    inputs.push({ name: key, type: types.Message }, { name: `${key}-at`, type: temporalTypes.instant });
    bindings[key] = { kind: "record", id: `${id}.${key}` }; bindings[`${key}-at`] = at.ref;
    operations.push({ id: key, producer: producers.append, inputs: { messages: operation(previous), message: input(key), at: input(`${key}-at`), timeline: input("timeline") }, result: { kind: "output", name: "messages" } });
    previous = key;
  }
  if (!index) throw new Error("Chat Scene requires a Message.");
  operations.push({ id: "render", producer: producers.render, inputs: { messages: operation(previous), options: input("options"),
    timeline: input("timeline"), canvas: input("canvas"), font: input("font"), window: input("window"), ...Object.fromEntries(assetNames.map(name => [name,input(name)])) }, result: { kind: "output", name: "track" } });
  const fragment = sealGraphFragment({ inputs, operations, exports: [{ name: "track", type: compositionTypes.visualTrack, root: operation("render") }] });
  return { records, fragments: [...fragments, fragment], components: [...components,
    { id, fragment: fragment.id, inputs: bindings, outputs: { track: `${id}.track` }, range: element.range }], exports: [`${id}.track`] };
};
const declaration = { name: "scene", tag: "Scene", mode: "structured" as const,
  outputs: [compositionTypes.visualTrack, timelineTypes.track, temporalTypes.window, temporalTypes.instant, temporalTypes.windowSpec, temporalTypes.instantSpec, ...Object.values(types)],
  vocabulary: { summary: "A conversation whose message arrivals and scrolling form one visual scene.", attributes: [
    ...temporalContextAttributeVocabulary, ...temporalWindowAttributeVocabulary,
    ...["id", "title", "canvas", "font"].map(name => ({ name, kind: "expression" as const, required: true, summary: name })),
    { name: "entrance-frames", kind: "literal" as const, required: false, summary: "Arrival and scrolling duration; defaults to 10 frames." },
  ], children: [{ tag: "Message", cardinality: "many" as const, summary: "One authored message and the event that reveals it.", attributes: [
    ...["id", "sender", "text", "side"].map(name => ({ name, kind: "literal" as const, required: true, summary: name })), ...temporalInstantAttributeVocabulary,
  ] }], ports: [{ name: "track", type: compositionTypes.visualTrack, summary: "The complete conversation scene." }],
    example: '<chat:Scene id="chat" timeline={speech.timeline} canvas={canvas} font={font} during="program" title="Conversation"><chat:Message id="answer" sender="Maya" side="left" text="Here it is." at={story.moment.answer}/></chat:Scene>',
  },
};
export const hypitPackage = { format: "hypit.node-package@1" as const, modules: [{ manifest }], components: [component],
  hostFacets: [createMarkupSurfaceHostFacet({ module, declaration, handler: decodeSurface })] };
export default hypitPackage;
