Guide on aesp commands
######################

One may use dpgen2 through command line interface. A full documentation of the cli is found :ref:`here <cli>`.

Submit a workflow
-----------------

The aesp workflow can be submitted via the submit command

.. code:: console

    aesp submit input.json

where ``input.json`` is the input script. A guide of writing the script is found :ref:`here <input_script>`. When a workflow is submitted, a ID (WFID) of the workflow will be printed for later reference.

Check the status of a workflow
------------------------------

The status of stages of the workflow can be checked by the status command. It prints the indexes of the finished stages, iterations, and the accurate, candidate and failed ratio of explored configurations of each iteration.

show the progress of workflow
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

.. code:: console

    aesp status input.json WFID

Show the keys of steps
>>>>>>>>>>>>>>>>>>>>>>

.. code:: console

    aesp status input.json WFID -s

Resubmit a workflow
-------------------