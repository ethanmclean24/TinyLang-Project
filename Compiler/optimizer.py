"""Verify and optimize LLVM IR using the instructor's new-pass-manager approach."""

from llvmlite import binding as llvm


def optimize_ir(ir_text: str, level: int = 2) -> str:
    """Return verified IR after applying the selected O0–O3 pipeline."""
    if type(level) is not int or level not in (0, 1, 2, 3):
        raise ValueError("Optimization level must be 0, 1, 2, or 3")
    with llvm.parse_assembly(ir_text) as module:
        module.verify()
        if level == 0:
            return str(module)
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
        target = llvm.Target.from_default_triple()
        with target.create_target_machine(opt=level) as machine:
            module.data_layout = str(machine.target_data)
            with llvm.create_pipeline_tuning_options(speed_level=level) as options:
                with llvm.create_pass_builder(machine, options) as builder:
                    with builder.getModulePassManager() as manager:
                        manager.run(module, builder)
            module.verify()
            return str(module)
