struc_info_name = "info.json"
workflow_name = 'dlcsp'
stand_csp_mode = 'st-csp'
dp_csp_mode = 'dp-csp'
dflow_status = ["Succeeded", "Running", "Pending", "Failed", "Error"]
operator = {
    'generator': ['random_gen'],
    "mutation": ["strain_mut", "permutation_mut", "ripple_mut"],
	"crossover": ["plane_cross", 'cylinder_cross', 'sphere_cross']
}
