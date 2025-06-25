USER_PROMPT = f"""
    Theorems in Coq have the following structure: <theorem_name> : <proposition>. The theorem we want to prove is:
    Theorem {theorem_name} : {proposition}.

    ####

    The complete file context in which we are writing this proof is:
    {file_context}

    In more detail, at the beginning of the context, we have the following description of the proof objectives:
    {proof_objectives_description}

    The context also includes all relevant imports and definitions (i.e. reusable named terms, which can be values, functions, propositions, or even proofs) that are necessary for the proof. 
    For instance, an example import is:
    {import_statement}
    and an example definition is:
    {definition_statement}

    The context also includes lemmas (named propositions with proofs) that are relevant to the proof. Lemmas in Coq have the following format:
    Lemma <name> : <proposition>.
    Proof.
        <tactics>.
    Qed.
    
    An example of such a lemma in our context is:
    {lemma_statement}

    Lemmas in Coq are built with tactics, which are commands that guide Coq in constructing a proof term by breaking the goal into simpler subgoals. In our example lemma, an example of a tactic is:
    {tactic}

    % IF THERE ARE HINTS, INCLUDE THIS BLOCK%
    Finally, the context also includes hints, which are facts such as lemmas, constructors, or rewrite rules, that serve as suggestions for tactics to solve goals.
    An example of a hint in our context is:
    {hint_statement}
    %%%%%%%%%%%%%%%%%%%%%

    Together, the context and theorem statement provide all the necessary information to construct the proof of the theorem in Coq.
   """