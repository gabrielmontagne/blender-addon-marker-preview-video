from collections import namedtuple
from functools import reduce
import bpy
import re

def slugify(name):
    return re.sub(r'[\W_]+', '-', name)

Span = namedtuple('Span', 'frame name length', defaults=[1])

class DialogOperator(bpy.types.Operator):
    bl_idname = "object.dialog_operator"
    bl_label = "Simple Dialog Operator"

    my_float = bpy.props.FloatProperty(name="Some Floating Point")
    my_bool = bpy.props.BoolProperty(name="Toggle Option")
    my_string = bpy.props.StringProperty(name="String Value")

    def execute(self, context):

        message = "Popup Values: %f, %d, '%s'" % \
            (self.my_float, self.my_bool, self.my_string)

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
            out_path = f'//marker-frames/mark-{i:05d}-{slugify(span.name)}'
            scene.render.filepath = out_path
            scene.frame_current = span.frame
            bpy.ops.render.render(write_still=True, scene=scene.name)
            context.window_manager.progress_update(i)

        scene.render.filepath = original_out

        print('spans!', spans)

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
