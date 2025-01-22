from dpdispatcher import Machine, Resources, Task, Submission
from pathlib import Path
def make_submission(
        mdata_machine,
        mdata_resources,
        commands,
        work_path,
        run_tasks,
        group_size,
        forward_common_files,
        forward_files,
        backward_files,
        outlog,
        errlog,
        ):
        if mdata_machine.get("local_root", "./") != "./":
            raise RuntimeError("local_root must be './' in pycsp's machine.json.")

        abs_local_root = Path("./").absolute()

        abs_mdata_machine = mdata_machine.copy()

        abs_mdata_machine["local_root"] = abs_local_root

        machine = Machine.load_from_dict(abs_mdata_machine)
        resources = Resources.load_from_dict(mdata_resources)

        command = "&&".join(commands)

        task_list = []
        for ii in run_tasks:
            print(ii)
            input()
            task = Task(
                command=command,
                task_work_path=ii,
                forward_files=forward_files,
                backward_files=backward_files,
                outlog=outlog,
                errlog=errlog,
            )
            task_list.append(task)
        submission = Submission(
            work_base=work_path,
            machine=machine,
            resources=resources,
            task_list=task_list,
            forward_common_files=forward_common_files,
            backward_common_files=[],
        )
        return submission