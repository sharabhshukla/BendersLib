# BendersLib: A Benders Decomposition Library in Python

**BendersLib** ([benders.dev](https://benders.dev)) is a Python library that supports a range of Benders decomposition variants, including **Classical Benders Decomposition**, **Combinatorial Benders Decomposition**, **L-shaped Method**, **Integer L-shaped Method**, **Generalized Benders Decomposition**, and **Logic-based Benders Decomposition**. While BendersLib provides built-in implementations of these methods, it is designed to be extensible. Users can implement custom Benders decomposition methods by customizing **subproblem solvers** and **cut generators**, and defining **callback functions** for enhancement strategies. BendersLib is solver agnostic and has built-in interfaces for popular Mathematical Programming and Constraint Programming solvers. Its support for rapid prototyping and high extensibility are designed to meet the needs of both researchers and practitioners in Operations Research and related fields.

## Documentation

- BendersLib's documentation is available at [https://benders.dev](https://benders.dev).

## License

- BendersLib's source code is licensed under the [Apache-2.0 License](LICENSE).

## References

1. Benders, J. F. (1962). Partitioning procedures for solving mixed-variables programming problems. Numerische Mathematik, 4(1), 238–252. https://doi.org/10.1007/BF01386316
2. Codato, G., & Fischetti, M. (2006). Combinatorial Benders’ cuts for mixed-integer linear programming. Operations Research, 54(4), 756–766. https://doi.org/10.1287/opre.1060.0286
3. Geoffrion, A. M. (1972). Generalized Benders Decomposition. Journal of Optimization Theory and Applications, 10(4), 237–260. https://doi.org/10.1007/BF00934810
4. Van Slyke, R. M., & Wets, R. (1969). L-shaped linear programs with applications to optimal control and stochastic programming. SIAM Journal on Applied Mathematics, 17(4), 638–663. https://doi.org/10.1137/0117061
5. Laporte, G., & Louveaux, F. V. (1993). The integer L-shaped method for stochastic integer programs with complete recourse. Operations Research Letters, 13(3), 133–142. https://doi.org/10.1016/0167-6377(93)90002-X
6. Hooker, J. N., & Ottosson, G. (2003). Logic-based Benders Decomposition. Mathematical Programming, 96(1), 33–60. https://doi.org/10.1007/s10107-003-0375-9