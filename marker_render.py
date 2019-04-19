from collections import namedtuple
from functools import reduce
from os import path
import bpy
import re

def slugify(name):
    return re.sub(r'[\W_]+', '-', name)

Span = namedtuple('Span', 'frame name length', defaults=[1])

class DialogOperator(bpy.types.Operator):
    bl_idname = "object.dialog_operator"
    bl_label = "Simple Dialog Operator"

    override_images: bpy.props.BoolProperty(name="Override images", default=False)
    clear_vse_layer: bpy.props.BoolProperty(name="Clean VSE layer", default=True)
    vse_layer_id: bpy.props.IntProperty(name='VSE target layer index', default=1)

    def execute(self, context):

        scene = context.scene
        frame_start = scene.frame_start
        frame_end = scene.frame_end

        print(frame_start, '→', frame_end)

        def to_spans(acc, next):
            frame = next.frame

            if frame < frame_start: return acc
            if frame > frame_end: return acc

            if not len(acc) and frame > frame_start:
                print('synthetic first frame')
                acc =[ Span(frame_start, 'start') ]

            acc.append(Span(next.frame, next.name))
            return acc

        def assign_lengths(spans):
            def calculate_length(acc, next):
                i, (c, n) = next
                is_last = i == len(spans) - 2
                print(i, c, n, is_last, len(spans) - 2)

                acc.append(c._replace(length=n.frame - c.frame))
                if is_last:
                    acc.append(n._replace(length=frame_end - n.frame))
                return acc

            return reduce(calculate_length, enumerate(zip(spans[:-1], spans[1:])), [])

        spans = assign_lengths(reduce(to_spans, scene.timeline_markers, []))

        original_out = scene.render.filepath
        context.window_manager.progress_begin(0, len(spans))
        for i, span in enumerate(spans):
            out_path = f'//marker-frames/mark-{i:03d}-frame-{span.frame:06d}-{slugify(span.name)}.png'
            scene.render.filepath = out_path
            scene.frame_current = span.frame

            print('path', bpy.path.abspath(out_path))
            print('    path exists?', path.exists(bpy.path.abspath(out_path)))

            if path.exists(bpy.path.abspath(out_path)):
                print(f'File {out_path} already exists.')
                if self.override_images:
                    print('Override images, render')
                    bpy.ops.render.render(write_still=True, scene=scene.name)
                else:
                    print('Skip rerender')
            else:
                bpy.ops.render.render(write_still=True, scene=scene.name)

            edit_scene = bpy.data.scenes.get('edit')

            if edit_scene is not None:
                print('we have an edit scene, try to mount on VSE')
                print('... on layer', self.vse_layer_id)
                print(f'should {self.clear_vse_layer} clear layer.')

                edit_scene.sequence_editor_create()
                new_sequence = edit_scene.sequence_editor.sequences.new_image(
                    name=span.name,
                    filepath=bpy.path.relpath(out_path),
                    frame_start=span.frame,
                    channel=self.vse_layer_id
                )
                new_sequence.frame_final_duration = span.length
                print('sequence', new_sequence)

            context.window_manager.progress_update(i)

        scene.render.filepath = original_out

        message = f'Done! renderered {len(spans)} marker images'

        self.report({'INFO'}, message)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

def register():
    bpy.utils.register_class(DialogOperator)

def unregister():
    bpy.utils.unregister_class(DialogOperator)

if __name__ == "__main__":
    register()
    print('\n' * 5)
    bpy.ops.object.dialog_operator('INVOKE_DEFAULT')
