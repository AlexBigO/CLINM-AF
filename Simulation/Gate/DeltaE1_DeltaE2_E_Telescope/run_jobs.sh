#!/bin/bash

/usr/bin/time -o ./Test/log_Test_RunTest_proton_wo_target_MC_log_Test_RunTest_proton_on_PMMA_MC_01.txt python3 simulation.py cfg_simulation_example.yml -id 01 >& ./Test/log_Test_RunTest_proton_wo_target_MC_log_Test_RunTest_proton_on_PMMA_MC_01.txt &
/usr/bin/time -o ./Test/log_Test_RunTest_proton_wo_target_MC_log_Test_RunTest_proton_on_PMMA_MC_02.txt python3 simulation.py cfg_simulation_example.yml -id 02 >& ./Test/log_Test_RunTest_proton_wo_target_MC_log_Test_RunTest_proton_on_PMMA_MC_02.txt &
/usr/bin/time -o ./Test/log_Test_RunTest_proton_wo_target_MC_log_Test_RunTest_proton_on_PMMA_MC_03.txt python3 simulation.py cfg_simulation_example.yml -id 03 >& ./Test/log_Test_RunTest_proton_wo_target_MC_log_Test_RunTest_proton_on_PMMA_MC_03.txt &
