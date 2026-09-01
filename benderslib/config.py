# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

config = {
    'PYOMO_OPTIONS': {
        'gurobi': {
            'OutputFlag': 0,
            'LogToConsole': 0,
            'InfUnbdInfo': 1,
            'QCPDual': 1,
        },
        'gurobi_direct': {
            'OutputFlag': 0,
            'LogToConsole': 0,
            'InfUnbdInfo': 1,
            'QCPDual': 1,
        },
        'gurobi_persistent': {
            'OutputFlag': 0,
            'LogToConsole': 0,
            'InfUnbdInfo': 1,
            'QCPDual': 1,
        },
        'scip': {
            'presolving/maxrounds': 0,
            'separating/maxrounds': 0,
            'propagating/maxrounds': 0,
            'lp/alwaysgetduals': True,
        },
    },
    'GUROBI_OPTIONS': {
        'OutputFlag': 0,  # Hide solver output
        'LogToConsole': 0,  # Hide solver output
        'InfUnbdInfo': 1,  # Get Model.FarkasDual requires InfUnbdInfo = 1
        'QCPDual': 1,  # QCPi requires QCPDual = 1
        'DualReductions': 0,  # Gurobi model status code 4 (INF_OR_UNBD)
    },
    'SCIP_OPTIONS': {
        'lp/alwaysgetduals': True,  # Get Farkas duals for infeasible problems
    },
    'CPLEXCP_OPTIONS': {
        'log_output': None,  # Hide solver output
    },
    'COPT_OPTIONS': {
        'Logging': 0,  # Hide solver output
        'LogToConsole': 0,  # Hide solver output
        'ReqFarkasRay': 1,  # Request Farkas dual for infeasible problems
    },
    'CPLEX_OPTIONS': {
        'preprocessing.presolve': 0,  # Parameters for obtaining Farkas certificate
        'lpmethod': 2,  # Parameters for obtaining Farkas certificate
    },
    'JAXIPM_OPTIONS': {
        # Overrides applied on top of jaxipm.default_params(). Keys must match
        # entries in jaxipm's IPOPT-style parameter dict (see jaxipm/params.json).
    },
    'STATUS_CODES': {
        'COPT': {
            1: 'OPTIMAL',
            2: 'INFEASIBLE',
            3: 'UNBOUNDED',
        },
        'CPLEX': {
            1: 'OPTIMAL',
            101: 'OPTIMAL',
            3: 'INFEASIBLE',
            103: 'INFEASIBLE',
            2: 'UNBOUNDED',
            118: 'UNBOUNDED',
            102: 'OPTIMAL',  # OPTIMAL_TOL
        },
        'CPLEXCP': {
            'optimal': 'OPTIMAL',
            'infeasible': 'INFEASIBLE',
            'feasible': 'OPTIMAL',  # FEASIBLE
        },
        'GUROBI': {
            2: 'OPTIMAL',
            3: 'INFEASIBLE',
            5: 'UNBOUNDED',
        },
        'JAXIPM': {
            # jaxipm.solver.TerminationCode values.
            0: 'UNKNOWN',  # CONTINUE (should not be observed after the solve loop exits)
            1: 'OPTIMAL',  # CONVERGED
            2: 'TIMEOUT',  # MAX_ITER_EXCEEDED
            3: 'ERROR',  # TINY_STEP_BREAK (numerical stall)
            4: 'INFEASIBLE',  # RESTORATION_FAILURE (feasibility restoration could not find a feasible point)
            5: 'OPTIMAL',  # ACCEPTABLE_POINT (converged to IPOPT's looser "acceptable" tolerance)
        },
        'ORTOOLS': {
            4: 'OPTIMAL',
            3: 'INFEASIBLE',
            2: 'OPTIMAL',  # FEASIBLE
        },
        'SCIP': {
            'optimal': 'OPTIMAL',
            'infeasible': 'INFEASIBLE',
            'unbounded': 'UNBOUNDED',
        },
        'PYOMO': {
            'optimal': 'OPTIMAL',
            'infeasible': 'INFEASIBLE',
            'unbounded': 'UNBOUNDED',
            'infeasibleOrUnbounded': 'UNBOUNDED',  # Treat 'infeasibleOrUnbounded' as 'UNBOUNDED'
        },
    },
}
