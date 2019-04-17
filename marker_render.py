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
    bpy.ops.object.dialog_operator('INVOKE_DEFAULT')
