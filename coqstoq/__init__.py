import sys
SUBMODULES = ['/home/t-ilshapiro/CoqStoq/coqstoq', 
               '/home/t-ilshapiro/CoqStoq/coqpyt',
               '/home/t-ilshapiro/CoqStoq/coqpyt/coqpyt',
               '/home/t-ilshapiro/CoqStoq/coqpyt/coqpyt/coq',
               '/home/t-ilshapiro/CoqStoq/coqpyt/coqpyt/coq/lsp',
               '/home/t-ilshapiro/CoqStoq/coqpyt/coqpyt/coq/tests',
               '/home/t-ilshapiro/CoqStoq/coqpyt/coqpyt/lsp',
               '/home/t-ilshapiro/CoqStoq/coqpyt/coqpyt/tests']

# SUBMODULES = [
#     '/app/coqstoq',
#     '/app/coqpyt',
#     '/app/coqpyt/coqpyt',
#     '/app/coqpyt/coqpyt/coq',
#     '/app/coqpyt/coqpyt/coq/lsp',
#     '/app/coqpyt/coqpyt/coq/tests',
#     '/app/coqpyt/coqpyt/lsp',
#     '/app/coqpyt/coqpyt/tests',
# ]

for MODULE in SUBMODULES:
    if MODULE not in sys.path:
        sys.path.append(MODULE)

