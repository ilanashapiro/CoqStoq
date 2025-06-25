USER_PROMPT = 
    """
        
        The type of the term is:\n```\nval test : phi: Prims.logical -> psi: Prims.logical -> xi: Prims.logical -> Prims.unit\n```\n#####\n\n
        
        The file context where I am writing this term is:
        \n```\nmodule Logic\n\nopen FStar.Tactics.V2\n\nlet tau () : Tac unit =\n    let h = implies_intro () in\n    right ();\n    let (h1, _) = destruct_and (binding_to_term h) in\n    apply (`FStar.Squash.return_squash);\n    exact (binding_to_term h1);\n    qed ()\n```\n#####\n\n
        
        A premise is other terms either defined in the same file or imported from other files.
        \nHere are complete type and definition of the premises in the input type:
        \n\n// Premise:  Prims.logical\n// Premise End\n\n\n// Premise:  Prims.unit\n// Premise End\n\n#####\n\n
        
        Here are complete type and definition of the other premises. These premises are used to define the terms that make up the current input type:\n\n// Premise:  Prims.eqtype\n// Premise End\n\n#####\n\n
        
        Here are some related examples with both the type and corresponding definition:\n// Example 1:\n\nval ex5 : p: Prims.prop -> q: Prims.prop -> Prims.unit\n\nlet ex5 (p q : prop) =\n  assert (p ==> p \\/ q)\n      by (let bp = implies_intro () in\n          left ();\n          hyp (binding_to_namedv bp);\n          qed ())\n\n// End of example 1\n\n// Example 2:\n\nval ex4 : p: Prims.prop -> q: Prims.prop -> Prims.unit\n\nlet ex4 (p q : prop) =\n  assert (p /\\ q ==> p)\n      by (let h = implies_intro () in\n          let (bp, bq) = destruct_and (binding_to_term h) in\n          hyp (binding_to_namedv bp);\n          qed ())\n\n// End of example 2\n\n#####\n\n\n\n\n
        
        Given the above information, please provide the definition of the following type:\n```\nval test : phi: Prims.logical -> psi: Prims.logical -> xi: Prims.logical -> Prims.unit\n```\n\n\nStart the definition with \n```\nlet test phi psi xi =\n```\n\n
        """