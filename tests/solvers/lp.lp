\ This Linear Programming model is designed to satisfy the following properties:
\
\ 1. Two continuous variables (x1, x2)
\ 2. Variables have upper and lower bounds
\ 3. Two constraints (c1, c2)
\ 4. Has the only optimal solution (2, 2), with objective value 12
\ 5. The dual variable values are (1, 1, 0, 0)
\ 6. After adding the constraint (c3: x1 + x2 <= 3), the model is infeasible
\    and has a unique IIS (c1, c2, c3) with all the variables being involved;
\    and a unique dual extreme ray (-0.333333, -0.333333, 1.0, 0.0, 0.0)

Minimize
 obj: 3 x1 + 3 x2
Subject To
 c1: x1 + 2 x2 >= 6
 c2: 2 x1 + x2 >= 6
Bounds
 0 <= x1 <= 100
 0 <= x2 <= 100
End
