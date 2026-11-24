"""Execute generated StudyLang LLVM IR with the instructor's MCJIT approach."""

import ctypes

from llvmlite import binding as llvm

from codegen import RUNTIME_ERRORS
from interpreter import StudyLangRuntimeError


_OUTPUT_TYPES = {
    "studylang_show_integer": ctypes.c_int64,
    "studylang_show_float": ctypes.c_double,
    "studylang_show_boolean": ctypes.c_int32,
}


def run_ir(ir_text: str, output=print) -> int:
    """Verify a compiler-produced module and execute its native main function."""
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()
    llvm.check_jit_execution()
    machine = llvm.Target.from_default_triple().create_target_machine()
    errors = []

    def emit(value, boolean=False):
        try:
            text = str(bool(value)).lower() if boolean else str(value)
            output(text)
        except Exception as error:
            # Python exceptions must be carried back across the native call boundary.
            errors.append(error)
            return 5
        return 0

    callbacks = {
        name: ctypes.CFUNCTYPE(ctypes.c_int32, kind)(
            lambda value, boolean=(name == "studylang_show_boolean"): emit(value, boolean)
        )
        for name, kind in _OUTPUT_TYPES.items()
    }
    with llvm.parse_assembly(ir_text) as module:
        module.verify()
        module.data_layout = str(machine.target_data)
        with llvm.create_mcjit_compiler(module, machine) as engine:
            # Bind output per engine and keep callbacks alive until execution ends.
            for name, callback in callbacks.items():
                engine.add_global_mapping(
                    module.get_function(name), ctypes.cast(callback, ctypes.c_void_p).value
                )
            engine.finalize_object()
            address = engine.get_function_address("main")
            if not address:
                raise StudyLangRuntimeError("LLVM module has no main entry point")
            status = ctypes.CFUNCTYPE(ctypes.c_int32)(address)()
    if errors:
        raise errors[0]
    if status:
        raise StudyLangRuntimeError(RUNTIME_ERRORS.get(status, f"Unknown LLVM runtime status: {status}"))
    return status
