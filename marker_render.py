from collections import namedtuple
from functools import reduce
from os import path
import bpy
import re

bl_info = {
    'name': 'Generate Preview from Marker renderers',
    'author': 'gabriel montagné, gabriel@tibas.london',
    'version': (0, 1, 0),
    'blender': (2, 80, 0),
    'description': 'Render all the frames with markers in them, and add the images to the VSE edit scene',
    'tracker_url': 'https://github.com/gabrielmontagne/blender-addon-marker-preview-video/issues',
    'category': 'Render'
}


def slugify(name):
    return re.sub(r'[\W_]+', '-', name)

Span = namedtuple('Span', 'frame name length', defaults=[1])

class RENDER_MARKER_OT_preview(bpy.types.Operator):

    bl_idname = "anim.preview_from_markers"
    bl_label = "Preview from markers"

    override_images: bpy.props.BoolProperty(name="Override images", default=False)
    clear_vse_channel: bpy.props.BoolProperty(name="Clean VSE channel", default=True)
    vse_channel_id: bpy.props.IntProperty(name='VSE target channel index', default=1)

    def execute(self, context):

        scene = context.scene
        frame_start = scene.frame_start
        frame_end = scene.frame_end

        def to_spans(acc, next):
            frame = next.frame

            if frame < frame_start: return acc
            if frame > frame_end: return acc

            if not len(acc) and frame > frame_start:
                acc =[ Span(frame_start, 'start') ]

            acc.append(Span(next.frame, next.name))
            return acc

        def assign_lengths(spans):
            def calculate_length(acc, next):
                i, (c, n) = next
                is_last = i == len(spans) - 2

                acc.append(c._replace(length=n.frame - c.frame))
                if is_last:
                    acc.append(n._replace(length=frame_end - n.frame))
                return acc

            return reduce(calculate_length, enumerate(zip(spans[:-1], spans[1:])), [])

        def to_frame(maker):
            return maker.frame

        spans = assign_lengths(reduce(to_spans, sorted(scene.timeline_markers, key=to_frame), []))

        edit_scene = bpy.data.scenes.get('Edit') or bpy.data.scenes.get('edit')
        if edit_scene is not None:

            print('we have an edit scene, try to mount on VSE')
            print('... on channel', self.vse_channel_id)
            print(f'should {self.clear_vse_channel} clear channel.')

            edit_scene.sequence_editor_create()
            sequence_editor = edit_scene.sequence_editor

            if self.clear_vse_channel:
                for s in list(sequence_editor.sequences):
                    if s.channel == self.vse_channel_id:
                        print('Removing sequence', s)
                        sequence_editor.sequences.remove(s)

        original_out = scene.render.filepath
        context.window_manager.progress_begin(0, len(spans))
        for i, span in enumerate(spans):
            out_path = f'//marker-frames/mark-{i:03d}-frame-{span.frame:06d}-{slugify(span.name)}.png'
            scene.render.filepath = out_path
            scene.frame_current = span.frame

            if path.exists(bpy.path.abspath(out_path)):
                print(f'File {out_path} already exists.')
                if self.override_images:
                    print('Override images, render')
                    bpy.ops.render.render(write_still=True, scene=scene.name)
                else:
                    print('Skip rerender')
            else:
                bpy.ops.render.render(write_still=True, scene=scene.name)


            if edit_scene is not None:
                new_sequence = sequence_editor.sequences.new_image(
                    name=span.name,
                    filepath=bpy.path.relpath(out_path),
                    frame_start=span.frame,
                    channel=self.vse_channel_id
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
    bpy.utils.register_class(RENDER_MARKER_OT_preview)

def unregister():
    bpy.utils.unregister_class(RENDER_MARKER_OT_preview)

if __name__ == "__main__":
    register()
    bpy.ops.anim.preview_from_markers('INVOKE_DEFAULT')
