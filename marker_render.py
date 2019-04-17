from functools import reduce
import bpy


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

        for m in scene.timeline_markers:
            print('m', m.camera, m.frame, m.name)

        def to_spans(acc, next):
            frame = next.frame
            is_first = not len(acc)

            if is_first and frame > frame_start:

                print(f'0-{frame}-')
                acc =[ { 'frame': frame_start, 'name': 'start', 'length': frame - frame_start } ]

            print('----', next)

            span = {
                'frame': next.frame,
                'name': next.name
            }

            acc.append(span)
            return acc

        spans = reduce(to_spans, scene.timeline_markers, [])
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
