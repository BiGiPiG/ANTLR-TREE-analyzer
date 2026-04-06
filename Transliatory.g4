grammar Transliatory;

// ── Правила парсера ──────────────────────────────────────────────
start      : expr* EOF ;  // Принимаем 0 или более выражений
expr       : simpleExpr assignTail ;
assignTail : '=' expr | ;
simpleExpr : incTail operand incTail ;
incTail    : '++' incTail | ;
operand    : VAR | INT ;

// ── Правила лексера ──────────────────────────────────────────────
INT        : [0-9]+ ;
VAR        : [a-zA-Z_][a-zA-Z0-9_]* ;
NEWLINE    : [\r\n]+ -> skip ;