# Flashcards: Arquitectura de Computadoras

**Total Cards:** 158
**Sources Processed:** Resumen Práctico Completo Arqui.pdf

**Generated:** 2025-10-16

---

## Tema 1: Representaciones de Datos

### Q: ¿Qué es un bit?

**A:** Un bit es un símbolo que puede tomar el valor 0 o 1. Es la unidad básica de información en sistemas digitales.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 2

---

### Q: ¿Qué es un byte?

**A:** Un byte es una colección ordenada de 8 bits. Es la unidad fundamental de almacenamiento en la mayoría de sistemas computacionales.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 2

---

### Q: ¿Qué es un código binario?

**A:** Un código binario es un conjunto ordenado de bits que se utiliza para representar información en sistemas digitales.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 2

---

### Q: ¿Cómo se define la distancia entre dos códigos binarios?

**A:** La distancia entre el código binario A y el código binario B es el número de bits que hay que cambiar en A para llegar a B. Por ejemplo, la distancia entre 1010 y 1110 es 1.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 2

---

### Q: ¿Qué es la distancia d de un sistema de codificación binario?

**A:** La distancia d es la menor de las distancias entre todos los códigos del sistema. Esta propiedad determina las capacidades de detección y corrección de errores del sistema.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 2

---

### Q: ¿Cuál es la condición para detectar errores en un sistema de codificación?

**A:** Es posible detectar errores cuando `t < d`, donde t es la cantidad máxima de bits modificados y d es la distancia del sistema. Esto asume que la probabilidad de falla es baja y las fallas son independientes.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 2

---

### Q: ¿Cuál es la condición para corregir errores en un sistema de codificación?

**A:** Es posible corregir errores cuando `t < d/2`, donde t es la cantidad máxima de bits modificados y d es la distancia del sistema.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 2

---

### Q: ¿En qué consiste el método de la paridad para detección de errores?

**A:** Se agregan bits controladores de la paridad del código para detectar errores. Para corregir errores, se puede implementar la paridad vertical, donde se controla la paridad por fila y por columna.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 2

---

### Q: ¿Cuántos bits de redundancia se necesitan para generar códigos de distancia d=3?

**A:** Para generar códigos de distancia d=3 para objetos representables en k bits, se necesitan utilizar p bits adicionales tal que `2^p ≥ p + k + 1`.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 2

---

### Q: ¿Cómo funcionan los códigos de Hamming?

**A:** Para un código `a₄a₃a₂a₁` se agregan bits de redundancia `p₃p₂p₁` calculando: `p₁ = a₄ ⊕ a₂ ⊕ a₁`, `p₂ = a₄ ⊕ a₃ ⊕ a₁`, `p₃ = a₄ ⊕ a₃ ⊕ a₂`. Luego se calcula s como combinación XOR de posiciones específicas. Si s=0 no hay errores; si s=x, indica la posición del bit errado.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 2

---

### Q: ¿Qué son los códigos de redundancia cíclica (CRC)?

**A:** Se define un polinomio M(x) de grado m-1 cuyos coeficientes coinciden con los bits del mensaje, y un polinomio G(x) de grado r. Se calcula `x^r·M(x) = Q(x)·G(x) + R(x)` y se envía T(x) = `x^r·M(x) + R(x)`. Si T(x) es divisible por G(x), el código es correcto.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 3

---

### Q: ¿Cómo se representa el tipo carácter internamente?

**A:** Se representan asociando un código binario distinto para cada carácter distinto según estándares. Los más usados actualmente son ISO 10646 y UNICODE.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 3

---

### Q: ¿Cuáles son las tres formas de implementar un string?

**A:** 1) De largo fijo, 2) De largo indeterminado indicando el final con un carácter especial, 3) Un registro de dos campos: el primero contiene el largo y el segundo la cadena de caracteres.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 3

---

### Q: ¿Cuántos números se pueden representar con n bits en enteros sin signo?

**A:** Con n bits se pueden representar `2^n` números, desde 0 hasta `2^n - 1`. Esta representación preserva el orden y las operaciones coinciden con lo que representan.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 3

---

### Q: ¿Cómo funciona la representación de valor absoluto y signo?

**A:** Se utilizan todos los bits disponibles menos 1 para almacenar el número, y el bit restante para almacenar el signo. Permite representar `-(2^(n-1) - 1)` a `2^(n-1) - 1`. Tiene dos representaciones para el cero.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 3

---

### Q: ¿Cómo funciona la representación por desplazamiento?

**A:** Aplica un desplazamiento d (típicamente `d = 2^(n-1)` o `d = 2^(n-1) - 1`) al número en binario: N → N + d. Permite representar `-d ≤ N ≤ 2^n - 1 - d`. Preserva el orden pero las operaciones no coinciden.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 3

---

### Q: ¿Cómo funciona la representación en complemento a uno?

**A:** Los números positivos se representan en binario, y los negativos como el complemento de cada bit del positivo correspondiente. Permite representar `-(2^(n-1) - 1)` a `2^(n-1) - 1`. Tiene dos representaciones para el cero.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 3

---

### Q: ¿Cómo funciona la representación en complemento a dos?

**A:** Representa los números por complemento a uno y luego le suma 1. Permite representar `-2^(n-1)` a `2^(n-1) - 1`. Tiene una única representación para el cero y las operaciones coinciden con lo representado.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 3

---

### Q: Compara las propiedades de las representaciones de enteros con signo

**A:** **Valor absoluto y signo:** 2 ceros, orden no preservado, operaciones no coinciden. **Desplazamiento:** 1 cero, orden preservado, operaciones no coinciden. **Complemento a uno:** 2 ceros, orden no preservado, operaciones no coinciden. **Complemento a dos:** 1 cero, orden no preservado, operaciones coinciden.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 4

---

### Q: ¿Qué es el problema de overflow en representación de enteros?

**A:** El overflow está dado por el bit de acarreo (carry bit), que es el bit más significativo "sobrante" de la operación cuando el resultado excede la capacidad de representación.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 3

---

### Q: ¿Qué es la representación decimal empaquetado?

**A:** Se representa el número como un string de caracteres: un número se representa como una sucesión de caracteres que son símbolos numéricos. El final del carácter implementado se indica con un carácter especial.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 4

---

### Q: ¿Cómo se representa un número en punto flotante?

**A:** N se representa como `N = (-1)^s · b^e · M`, donde s es el signo, e el exponente, M la mantisa, y b la base. Generalmente en base 2: `N = (-1)^s · 1.F · 2^E` y se almacena la terna (S, F, E) según el estándar IEEE 754.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 4

---

### Q: ¿Qué diferencia hay entre un número normalizado y denormalizado en punto flotante?

**A:** Un número está **normalizado** si la mantisa es 1.F (el bit más significativo es 1). Está **denormalizado** si la mantisa es 0.F. La normalización maximiza la mantisa tomando su bit más significativo distinto de 0.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 4

---

## Tema 2: Álgebra de Boole

### Q: ¿Cuál es el primer axioma del Álgebra de Boole?

**A:** Existe un conjunto G de objetos, sujetos a una relación de equivalencia denotada por "=" que satisface el principio de sustitución.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 5

---

### Q: ¿Qué establece el axioma de las reglas de combinación en Álgebra de Boole?

**A:** Se definen dos operaciones "+" (suma) y "·" (producto) tal que para todo a, b en G: `a + b ∈ G` y `a · b ∈ G`. Es decir, el conjunto es cerrado bajo estas operaciones.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 5

---

### Q: ¿Cuál es el axioma de los elementos neutros en Álgebra de Boole?

**A:** Existe un elemento 0 tal que para cada a en G: `a + 0 = a`. Existe un elemento 1 tal que para cada a en G: `a · 1 = a`.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 5

---

### Q: ¿Qué establece el axioma conmutativo del Álgebra de Boole?

**A:** Para todo a, b en G ocurre que `a + b = b + a` y `a · b = b · a`. El orden de los operandos no altera el resultado.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 5

---

### Q: ¿Qué establece el axioma distributivo del Álgebra de Boole?

**A:** Para todo a, b, c en G: `a + (b · c) = (a + b) · (a + c)` y `a · (b + c) = (a · b) + (a · c)`. Cada operación se distribuye sobre la otra.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 5

---

### Q: ¿Qué establece el axioma del complemento en Álgebra de Boole?

**A:** Para todo a en G, existe ā tal que `ā · a = 0` y `ā + a = 1`. Cada elemento tiene un complemento.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 5

---

### Q: ¿Qué establece la propiedad de dualidad en Álgebra de Boole?

**A:** Todo enunciado válido posee un dual también válido intercambiando "0" por "1" y "+" por "·" simultáneamente.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 5

---

### Q: ¿Qué establece la propiedad de asociatividad en Álgebra de Boole?

**A:** `a + (b + c) = (a + b) + c` y `a · (b · c) = (a · b) · c`. Los paréntesis pueden moverse sin cambiar el resultado.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 5

---

### Q: ¿Qué establece la propiedad de idempotencia en Álgebra de Boole?

**A:** `a + a = a` y `a · a = a`. Combinar un elemento consigo mismo devuelve el mismo elemento.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 5

---

### Q: ¿Qué establecen las propiedades de neutros cruzados?

**A:** `a + 1 = 1` y `a · 0 = 0`. El elemento 1 absorbe en la suma y el 0 absorbe en el producto.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 5

---

### Q: ¿Qué establece la propiedad de doble complemento?

**A:** El complemento del complemento de a es a: `ā̄ = a`. También: `a + ab = a` y `a + āb = a + b`.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 5

---

### Q: ¿Qué establece la Ley de De Morgan?

**A:** El complemento de una suma es el producto de los complementos, y viceversa: `a + b = ā · b̄` (negando ambos lados: `(a + b)‾ = ā · b̄`).

**Source:** Resumen Práctico Completo Arqui.pdf, Página 5

---

### Q: ¿Cuál es el modelo lógico del Álgebra de Boole?

**A:** G = {V, F} con las operaciones ∨ (OR), ∧ (AND) y negación. El isomorfismo es: V↔1, F↔0, ∧↔·, ∨↔+.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 5

---

### Q: ¿Cuál es el modelo circuital del Álgebra de Boole?

**A:** G = {A, C} donde A es circuito abierto y C es circuito cerrado. El isomorfismo es: A↔0, C↔1, circuito en paralelo↔+, circuito en serie↔·.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 6

---

### Q: ¿Cuál es el modelo binario del Álgebra de Boole?

**A:** G = {0, 1} con operaciones AND y OR. El isomorfismo es: 0↔0, 1↔1, OR↔+, AND↔·. Este es el modelo que se utilizará en el resto del curso.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 6

---

### Q: ¿Qué es la operación XOR?

**A:** XOR (OR exclusivo) es equivalente a "distinto" o "no igual". Devuelve 1 cuando los operandos son diferentes: 0 XOR 0 = 0, 0 XOR 1 = 1, 1 XOR 0 = 1, 1 XOR 1 = 0.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 6

---

### Q: ¿Qué es la operación NAND?

**A:** NAND es la negación del AND. Devuelve 0 solo cuando ambos operandos son 1: 0 NAND 0 = 1, 0 NAND 1 = 1, 1 NAND 0 = 1, 1 NAND 1 = 0.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 6

---

### Q: ¿Qué es la operación NOR?

**A:** NOR es la negación del OR. Devuelve 1 solo cuando ambos operandos son 0: 0 NOR 0 = 1, 0 NOR 1 = 0, 1 NOR 0 = 0, 1 NOR 1 = 0.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 6

---

### Q: ¿Cómo se define una función booleana por extensión?

**A:** Una función `F: G^n → G` se define por extensión mediante una tabla llamada "tabla de verdad" que especifica el valor de salida para cada posible combinación de entradas.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 6

---

### Q: ¿Cómo se define una función booleana por comprensión?

**A:** Una función `F: G^n → G` se define por comprensión indicando los puntos donde se anula `F = Σ(a₁,...,aₙ)` o los puntos donde no se anula `F = Π(b₁,...,bₙ)`.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 6

---

### Q: Enuncia el teorema de la expresión algebraica para funciones booleanas

**A:** Toda función booleana f de n variables puede expresarse como la suma de productos: `f(x₁,...,xₙ) = x₁x₂x₃···xₙ·f(1,1,1,...,1) + x₁x₂x̄₃···xₙ·f(0,1,1,...,1) + ... + x̄₁x̄₂x̄₃···x̄ₙ·f(0,0,0,...,0)`.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 6

---

### Q: ¿Cómo se obtiene la expresión algebraica de una función desde su tabla de verdad?

**A:** La expresión algebraica se obtiene como la suma de los productos de las variables (conjugando según sea necesario para que el producto no se anule con esas entradas) para todas las filas donde la función no se anula (vale 1).

**Source:** Resumen Práctico Completo Arqui.pdf, Página 6

---

### Q: ¿Cuáles son las propiedades para simplificación algebraica de funciones?

**A:** 1) `f·f̄ = 0`, 2) `f + f̄ = 1`, 3) `gf + gf̄ = f`, 4) `gf + f̄ = f`, 5) `f + f̄g = f + g`.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 6

---

### Q: ¿Cuál es el procedimiento para crear un Mapa de Karnaugh de 3-4 variables?

**A:** 1) Dibujar cuadrícula con columnas 00, 01, 11, 10 (para variables a,b) y filas para c o d. 2) Marcar con 1 donde la función vale 1. 3) Agrupar la mayor cantidad de unos cuya cantidad sea potencia de 2 (considerando que no tiene borde). 4) Sumar términos asociados a cada rectángulo (producto de variables cuyo valor no cambia en el rectángulo).

**Source:** Resumen Práctico Completo Arqui.pdf, Página 7

---

### Q: ¿Cómo se maneja un Mapa de Karnaugh de 5 variables?

**A:** Se hacen dos mapas de Karnaugh superpuestos. En uno se supone la quinta variable de valor 0 y en la otra de valor 1. Esto permite manejar las 32 combinaciones posibles.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 7

---

## Tema 3: Circuitos Combinatorios

### Q: ¿Qué es un circuito combinatorio?

**A:** Un circuito combinatorio se define como un circuito cuya salida está determinada en todo instante por la entrada actual. No tiene memoria de estados anteriores.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 8

---

### Q: ¿Cuáles son las compuertas lógicas básicas y sus símbolos?

**A:** Las compuertas básicas son NOT (inversor), AND (producto), OR (suma), NAND (AND negado), NOR (OR negado), y XOR (OR exclusivo). Cada una tiene representación triangular/curva y rectangular con sus símbolos correspondientes.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 8

---

### Q: ¿Qué son los bloques lógicos en circuitos?

**A:** Los bloques lógicos son representaciones compactadas de circuitos lógicos complejos. Se simbolizan como cajas rectangulares con entradas y salidas. Cuando se usan, debe especificarse cada salida `sᵢ = fᵢ(a₁,...,aₙ)`.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 8

---

### Q: ¿Qué es un circuito decodificador?

**A:** Un decodificador tiene N entradas y 2^N salidas. Dada una combinación de unos y ceros a la entrada, todas las salidas están en 0 salvo la que corresponde al número binario coincidente con la combinación de entrada.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 9

---

### Q: ¿Qué es un circuito multiplexor?

**A:** Un multiplexor tiene N + 2^N entradas y una salida. La salida Y toma el valor de la entrada de datos D cuyo índice coincida con el número binario representado por las entradas de control A, B, C. Funciona como selector de datos.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 10

---

### Q: ¿Qué diferencia hay entre entradas de control y de datos en un multiplexor?

**A:** Las **entradas de control** (A, B, C) determinan cuál entrada de datos se selecciona. Las **entradas de datos** (D0, D1, ..., D7) son las fuentes de información que pueden pasar a la salida según la selección.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 10

---

### Q: ¿Qué es un circuito demultiplexor?

**A:** Un demultiplexor recibe una señal de entrada G (Gate) y las entradas de control determinan por cuál salida Y se envía el valor de G. Es la operación inversa al multiplexor.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 10

---

### Q: ¿Qué es un sumador completo de 1 bit?

**A:** Suma dos números de un bit cada uno (a y b) con un acarreo de entrada (cᵢₙ) y devuelve la suma (s) y un acarreo de salida (cₒᵤₜ). Implementa la suma binaria completa de un dígito.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 12

---

### Q: ¿Cómo se construye un sumador completo de N bits?

**A:** Se conexionan en cascada sumadores completos de 1 bit. El acarreo de salida (cₒᵤₜ) de cada sumador se conecta al acarreo de entrada (cᵢₙ) del siguiente sumador, permitiendo sumar números de múltiples bits.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 13

---

### Q: ¿Qué es una ROM y cuál es su estructura?

**A:** Una ROM (Read-Only Memory) tiene m + 2 entradas y n salidas. Dada una entrada, devuelve n bits "almacenados" en esa dirección. CS (Chip Select) selecciona o deselecciona la ROM (si está deseleccionada, todas las salidas son 0).

**Source:** Resumen Práctico Completo Arqui.pdf, Página 13

---

### Q: ¿Cómo se implementa internamente una ROM?

**A:** Internamente usa un decodificador de m entradas a 2^m salidas, y cada salida se conecta a través de compuertas OR a las n líneas de datos de salida según el patrón deseado. El CS controla la habilitación de las salidas.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 13

---

### Q: ¿Qué es el retardo de conmutación en circuitos?

**A:** Es el tiempo de reacción debido a corrientes transitorias que causan resultados reales incorrectos temporalmente. También llamado tiempo de propagación o tiempo de setup.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 14

---

### Q: ¿Cómo se soluciona el problema del retardo de conmutación?

**A:** Se incorporan relojes (clocks) tras los cambios para que las salidas puedan tomarse como válidas solo después de que las corrientes transitorias se hayan disipado, garantizando lecturas correctas.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 14

---

### Q: ¿Qué es la lógica del tercer estado (tri-state)?

**A:** Agrega a los estados 0 y 1 el estado Z (alta impedancia). Con Z=1 se habilita la salida, con Z=0 se inhabilita. Se implementa con una entrada OE (Output Enabled) que controla si la salida está activa o en alta impedancia.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 14

---

## Tema 4: Circuitos Secuenciales

### Q: ¿Qué es un circuito secuencial?

**A:** Es un circuito cuya salida no depende solo de las entradas actuales, sino también de los valores de las entradas anteriores. Tiene "memoria" de estados previos.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 15

---

### Q: ¿Qué es un flip-flop?

**A:** Es un circuito capaz de "recordar" un valor de la entrada previa y por ello puede considerarse un "elemento de memoria". Es la unidad básica de almacenamiento en circuitos secuenciales.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 15

---

### Q: ¿Cómo funciona un flip-flop R-S asincrónico (Latch)?

**A:** Tiene entradas R (Reset) y S (Set). Cuando R=0 y S=1, Q=1. Cuando R=1 y S=0, Q=0. Cuando R=0 y S=0, mantiene el estado anterior. R=1 y S=1 es una condición no permitida.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 15

---

### Q: ¿Qué diferencia hay entre un flip-flop sincrónico y uno asincrónico?

**A:** Los **asincrónicos** (Latch) cambian inmediatamente cuando cambian las entradas. Los **sincrónicos** solo cambian cuando lo permite una señal de control G (generalmente proveniente de un reloj - CLK).

**Source:** Resumen Práctico Completo Arqui.pdf, Página 16

---

### Q: ¿Qué diferencia hay entre control por reloj y control por flanco de reloj?

**A:** **Control por reloj:** El acceso al contenido se habilita cuando G vale 1. **Control por flanco:** El acceso se habilita solo en los cambios de valor de G (flancos ascendentes o descendentes).

**Source:** Resumen Práctico Completo Arqui.pdf, Página 16

---

### Q: ¿Cómo funciona un flip-flop D?

**A:** El nuevo valor de la salida Q corresponde al valor de la entrada D mientras G está en 1. Mientras G está en 0, la salida mantiene el valor de D inmediatamente antes de la transición de 1 a 0 en G. Su ecuación característica es `Qₙ₊₁ = D`.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 17

---

### Q: ¿Cuándo se actualiza un flip-flop D con control por flanco?

**A:** Con control por flanco, se actualiza en el flanco ascendente del reloj (cuando el reloj va de 0 a 1). Esto permite sincronización precisa de las operaciones.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 17

---

### Q: ¿Cómo funciona un flip-flop T?

**A:** Mantiene su salida incambiada (T=0) o bien la invierte (T=1). Su ecuación característica es `Qₙ₊₁ = Q̄ₙT + QₙT̄`. Es útil para contadores y división de frecuencia.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 18

---

### Q: ¿Cómo funciona un flip-flop J-K?

**A:** Funciona bajo flancos descendentes de reloj. Cuando J=0 y K=0 mantiene el estado, J=0 y K=1 pone Q=0, J=1 y K=0 pone Q=1, J=1 y K=1 invierte Q. Su ecuación característica es `Qₙ₊₁ = JQ̄ₙ + K̄Qₙ`.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 18

---

### Q: ¿Cómo puede un flip-flop J-K emular otros tipos de flip-flops?

**A:** **R-S:** J=S, K=R. **D:** J=D, K=D̄. **T:** J=T, K=T. Esto hace al J-K un flip-flop universal que puede configurarse para comportarse como cualquier otro tipo.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 18

---

### Q: ¿Para qué sirven las entradas Set y Clear en los flip-flops?

**A:** Son entradas asincrónicas. **Set (o Preset):** Pone el flip-flop en 1 independientemente del reloj. **Clear:** Pone el flip-flop en 0 independientemente del reloj. Útiles para inicialización.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 19

---

### Q: ¿Qué es la entrada Clock Enabled (CE)?

**A:** Sirve para indicarle al flip-flop cuándo debe modificar el contenido. La información solo se guarda si CE=1 y hay un flanco de reloj. Evita escribir en el flip-flop cuando no interesa, pese a que ocurra un flanco de reloj.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 19

---

### Q: ¿Cómo funciona un contador regresivo con flip-flops T?

**A:** Se conectan flip-flops T en cascada con T=1 (siempre invertir). La salida Q de cada flip-flop se conecta al CLK del siguiente. Cada flanco de reloj decrementa el contador. El patrón va de 1111 hacia 0000.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 19

---

### Q: ¿Cómo funciona un contador progresivo con flip-flops T?

**A:** Similar al regresivo pero conectando la salida Q̄ al CLK del siguiente flip-flop. Cada flanco de reloj incrementa el contador. El patrón va de 0000 hacia 1111.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 20

---

### Q: ¿Cómo se modela matemáticamente un circuito secuencial?

**A:** Se modela como `Y = G(X, E)` y `E' = H(X, E)`, donde Y es la salida, X la entrada, E el estado interno, E' el próximo estado, y G y H son funciones. Corresponde a una máquina de Mealy.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 21

---

### Q: ¿Cuáles son los pasos para diseñar un circuito secuencial?

**A:** 1) Modelar con AFD mediante diagrama de estados, 2) Deducir tablas de salida y transición, 3) Determinar número de flip-flops y codificación, 4) Incorporar codificación a las tablas, 5) Determinar funciones lógicas, 6) Minimizar con Karnaugh, 7) Dibujar el circuito.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 21

---

### Q: ¿Qué es un contador basado en flip-flops D?

**A:** Cuenta según cada flanco de reloj de forma progresiva. Cada flip-flop D recibe como entrada una función lógica de los estados actuales que determina el siguiente bit del contador.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 20

---

## Tema 5: Máquinas de Estado

### Q: ¿Qué es un estado en un circuito secuencial?

**A:** Dadas dos secuencias de valores de entrada de un circuito secuencial, son equivalentes si a partir de cierto punto coinciden las entradas y las salidas. Cada clase de equivalencia que define esta relación es un estado.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 24

---

### Q: ¿Qué es un AFD (Autómata Finito Determinista)?

**A:** Es un modelo matemático de un sistema con entradas y salidas discretas que tiene el mismo comportamiento para la misma combinación entrada-salida. Es fundamental para el diseño de circuitos secuenciales.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 24

---

### Q: ¿Cómo se define formalmente una máquina de estado?

**A:** Son cuaternas `M = (E, e₀, Σ, δ)` donde E es el conjunto finito de estados, e₀ es el estado inicial (e₀ ∈ E), Σ es el alfabeto de entrada, y δ: E × Σ → E es la función de transición.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 24

---

### Q: ¿Qué es una Máquina de Mealy?

**A:** Se define como `M = (E, e₀, Σ, Δ, δ, λ)` donde Δ es el alfabeto de salida y λ: E × Σ → Δ es la función de salida. La salida está asociada con la transición (depende del estado actual y la entrada).

**Source:** Resumen Práctico Completo Arqui.pdf, Página 24

---

### Q: ¿Qué es una Máquina de Moore?

**A:** Se define como `M = (E, e₀, Σ, Δ, δ, λ)` donde λ: E → Δ. La salida está asociada con el estado (solo depende del estado actual, no de la entrada).

**Source:** Resumen Práctico Completo Arqui.pdf, Página 25

---

### Q: ¿Qué diferencia hay entre máquina de Mealy y máquina de Moore?

**A:** En **Mealy** la salida depende del estado actual y la entrada (`Y = G(X,E)`). En **Moore** la salida solo depende del estado actual (`Y = G(E)`). Mealy suele ser más compacta, Moore más fácil de diseñar.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 21 y 24-25

---

### Q: ¿Qué es una máquina lógica general?

**A:** Es una máquina que puede comportarse tanto como traductor de símbolos como reconocedora de secuencias. Puede resolver cualquier problema computable (admitido sin demostrar).

**Source:** Resumen Práctico Completo Arqui.pdf, Página 25

---

### Q: ¿Cuál es el diseño general de una máquina lógica general?

**A:** Consta de una ROM que recibe la entrada X y el estado E, y genera la salida Y. El estado E se almacena en una RAM que recibe el nuevo estado E' desde la ROM.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 25

---

### Q: ¿Cuál es el diseño de una máquina lógica general programable?

**A:** Similar a la general pero usando RAM en lugar de ROM. Esto permite que las funciones G y H sean programables (modificables), haciendo la máquina más versátil.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 25

---

## Tema 6: Computadora - Arquitectura de Von Neumann

### Q: ¿Qué es una computadora según la arquitectura de Von Neumann?

**A:** Es una máquina lógica general programable que puede resolver cualquier problema computable mediante la ejecución de programas almacenados en memoria.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 26

---

### Q: ¿Cuál es el concepto fundamental de la Arquitectura de Von Neumann?

**A:** Utiliza el concepto de que una operación compleja puede dividirse como una secuencia ordenada de operaciones más simples. Introdujo el "programa almacenado" como una "secuencia lógicamente ordenada de instrucciones".

**Source:** Resumen Práctico Completo Arqui.pdf, Página 26

---

### Q: ¿Cuáles son los tres bloques constructivos básicos de la arquitectura de Von Neumann?

**A:** **CPU:** Ejecuta los programas. **Memoria (MEM):** Almacena el programa y los datos. **Entrada/Salida (E/S):** Comunica el computador con los usuarios.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 26

---

### Q: ¿Cuáles son las variantes principales de la arquitectura de Von Neumann?

**A:** 1) Set de instrucciones, 2) Formato de instrucción, 3) Set de registros, 4) Modos de direccionamiento, 5) Manejo de la E/S, 6) Manejo de interrupciones. Cada variante afecta las capacidades y el desempeño del sistema.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 26

---

### Q: ¿Qué es la ALU (Unidad Aritmético-Lógica)?

**A:** Es un circuito lógico que implementa operaciones de aritmética binaria, operaciones lógicas y operaciones de desplazamiento o rotación de bits. Es donde se realizan los cálculos.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 26

---

### Q: ¿Qué es la UC (Unidad de Control)?

**A:** Es un circuito secuencial que implementa el "ciclo de instrucción", permitiendo acceder a la siguiente instrucción de un programa, leer sus operandos, efectuar la operación indicada en la ALU y guardar el resultado.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 26

---

### Q: ¿Qué es el Banco de Registros en una CPU?

**A:** Es una serie de posiciones de memoria ubicadas dentro de la propia CPU que permiten acceso a operandos y almacenamiento de resultados mucho más veloz que la memoria normal. Algunos son internos y otros utilizables por el programador.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 26

---

### Q: ¿Qué es un registro totalmente visible?

**A:** Contiene operandos o direcciones para la utilización en instrucciones. Es accesible al programador directamente a través de las instrucciones.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 27

---

### Q: ¿Qué es un registro parcialmente visible?

**A:** Contiene funciones especiales y es manipulado indirectamente por el programador para funciones específicas. Ejemplos: IP (Instruction Pointer), PC (Program Counter), SP (Stack Pointer), PS (Processor Status) y FLAGS.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 27

---

### Q: ¿Qué son los registros internos de la CPU?

**A:** Los utiliza la CPU para poder ejecutar las instrucciones. Almacenan constantes, el estado de la UC, la instrucción en ejecución y resultados intermedios de cálculos de direcciones. No son accesibles al programador.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 27

---

### Q: ¿Cuáles son las fases del ciclo de instrucción?

**A:** 1) **Fetch:** Leer la próxima instrucción de memoria, 2) **Decode:** Analizar el código binario, 3) **Read:** Acceder a memoria para operandos, 4) **Execute:** Ejecutar la operación en la ALU, 5) **Write:** Escribir el resultado en el destino.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 27

---

### Q: ¿Qué hace la fase Fetch del ciclo de instrucción?

**A:** Lee la próxima instrucción a ejecutarse desde la memoria. Utiliza el registro IP (Instruction Pointer) para saber qué dirección de memoria contiene la siguiente instrucción.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 27

---

### Q: ¿Qué hace la fase Decode del ciclo de instrucción?

**A:** Analiza el código binario de la instrucción para determinar qué se debe realizar: cuál operación ejecutar, qué operandos usar y dónde almacenar el resultado.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 27

---

### Q: ¿Qué hace la fase Execute del ciclo de instrucción?

**A:** Ejecuta la operación especificada en la ALU (Unidad Aritmético-Lógica) utilizando los operandos que fueron leídos en la fase Read.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 27

---

### Q: ¿Qué es el registro IP (Instruction Pointer)?

**A:** Almacena la dirección de memoria de la próxima instrucción a ejecutar. También llamado PC (Program Counter). Se incrementa automáticamente después de cada fetch.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 28

---

### Q: ¿Qué es el registro SP (Stack Pointer)?

**A:** Es el puntero a la pila (stack). Indica la dirección del tope de la pila, una estructura de datos LIFO usada para llamadas a funciones y almacenamiento temporal.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 28

---

### Q: ¿Qué es el registro PS (Processor Status)?

**A:** Almacena el estado del procesador, en particular los FLAGS (banderas) como Carry, Overflow y Zero que indican condiciones resultantes de operaciones aritméticas y lógicas.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 28

---

### Q: ¿Qué es el registro IR (Instruction Register)?

**A:** Almacena la instrucción leída desde memoria durante la fase Fetch. La Unidad de Control analiza este registro para determinar qué hacer en las fases siguientes.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 28

---

### Q: ¿Qué es el registro MAR (Memory Address Register)?

**A:** Contiene la dirección de memoria que se presenta en el bus de direcciones durante una operación de lectura o escritura de la memoria.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 28

---

### Q: ¿Qué es el registro MDR (Memory Data Register)?

**A:** Contiene el dato leído de la memoria (en una operación de lectura) o el dato a escribir en la memoria (en una operación de escritura). Actúa como buffer entre la CPU y la memoria.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 28

---

### Q: ¿Qué diferencia hay entre lógica cableada y lógica microprogramada?

**A:** **Lógica cableada:** La UC se construye como una Máquina de Mealy basada en diagrama de estados. **Lógica microprogramada:** Para cada instrucción existe un microprograma (secuencia de microinstrucciones) que establece el orden de eventos.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 30

---

### Q: ¿Qué diferencia hay entre microprogramación vertical y horizontal?

**A:** **Vertical:** Cada microinstrucción contiene los bits codificados de las señales de control. **Horizontal:** Utiliza microinstrucciones con los bits de control sin codificar (más directas pero más largas).

**Source:** Resumen Práctico Completo Arqui.pdf, Página 30

---

## Tema 6: Entrada/Salida (E/S)

### Q: ¿Qué es un bus?

**A:** Es una agrupación de "líneas" que comunican tres tipos de información en el computador: Dirección, Datos y Control. Permite la comunicación entre los diferentes componentes del sistema.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 30

---

### Q: ¿Qué es el bus de direcciones?

**A:** Son líneas de conexión que transportan las direcciones de memoria o E/S a ser accedidas durante una transferencia. Determina qué dispositivo o posición de memoria se está accediendo.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 30

---

### Q: ¿Qué es el bus de datos?

**A:** Son líneas de conexión que transportan la información que es transferida sobre el bus. Lleva los datos reales entre la CPU, memoria y dispositivos de E/S.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 30

---

### Q: ¿Qué señales incluye el bus de control?

**A:** Memory_Read, Memory_Write, I/O_Read, I/O_Write, Bus_Request, Bus_Grant, Transfer_ACK, Interrupt_Request, Interrupt_ACK, Clock y Reset. Controlan el uso del bus y la comunicación.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 30

---

### Q: ¿Para qué sirve la señal Bus_Request?

**A:** Indica que un sub-sistema desea tomar control del bus para iniciar una transferencia. Es parte del mecanismo de arbitraje del bus.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 30

---

### Q: ¿Para qué sirve la señal Bus_Grant?

**A:** Confirma que el bus está disponible para quien lo solicitó mediante Bus_Request. Permite al solicitante tomar control del bus.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 30

---

### Q: ¿Qué diferencia hay entre un bus simple y un bus inteligente?

**A:** **Bus simple (Master-Slave):** Una sola entidad (Master, generalmente la CPU) controla el bus y las demás son Slaves. **Bus inteligente:** Cualquier entidad puede ser potencialmente el Master mediante arbitraje.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 31

---

### Q: ¿Qué es el arbitraje centralizado de bus?

**A:** Hay una entidad con mayor jerarquía (generalmente la CPU) encargada de controlar el bus. Cada entidad interesada en ser el Master se lo solicita al árbitro.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 31

---

### Q: ¿Qué es el arbitraje distribuido de bus?

**A:** Todas las entidades conectadas tienen el mismo rango y no hay un árbitro: la inteligencia del bus se encuentra distribuida entre todos los participantes.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 31

---

### Q: ¿Qué diferencia hay entre buses internos y externos?

**A:** **Internos:** Se utilizan para conectar sub-sistemas dentro de la "frontera" del sistema (dentro del gabinete). **Externos:** Se utilizan para conectar sub-sistemas fuera de la "frontera" del sistema.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 31

---

### Q: ¿Qué son los periféricos?

**A:** Son dispositivos que realizan el vínculo del computador con el mundo exterior. A través de ellos se realiza el ingreso de programas y datos, se obtienen resultados en formato legible para el ser humano, o se provoca alteración del mundo físico circundante.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 31

---

### Q: ¿Qué es el controlador de un periférico?

**A:** Es la parte del periférico que contiene su inteligencia. Maneja la comunicación entre la CPU y el dispositivo físico, implementando el protocolo de comunicación necesario.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 31

---

### Q: ¿Cuáles son las posibles ubicaciones de un controlador?

**A:** 1) Contenido en el gabinete del computador (conectado directamente al bus o mediante adaptador), 2) Contenido en el gabinete del periférico (conectado mediante interfaz o adaptador), 3) Distribuido entre ambos gabinetes.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 32

---

### Q: ¿Cuáles son las dos arquitecturas para acceder a controladores?

**A:** 1) La CPU dispone de un espacio de direcciones reservado accedido mediante instrucciones especiales (E/S mapeada en puertos). 2) La CPU accede a los controladores como posiciones normales de memoria (E/S mapeada en memoria).

**Source:** Resumen Práctico Completo Arqui.pdf, Página 32

---

### Q: ¿Qué es un registro de solo lectura en un controlador?

**A:** El registro puede solamente ser leído; la escritura no surte efecto. Se usa típicamente para leer el estado del dispositivo o datos de entrada.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 33

---

### Q: ¿Qué es un registro de solo escritura en un controlador?

**A:** El registro solo puede ser escrito; la lectura tiene un resultado impredecible. Se usa típicamente para enviar comandos o datos de salida al dispositivo.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 33

---

### Q: ¿Qué es un registro de Lectura/Escritura independiente?

**A:** Hay dos registros diferentes en la misma dirección: uno para solo lectura y otro para solo escritura, que funcionan independientemente según la operación realizada.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 33

---

### Q: ¿Cuáles son los tipos de registros en un controlador?

**A:** **Entrada:** Dato destinado a la CPU. **Salida:** Dato destinado al periférico. **Estado:** Bits que indican el estado del controlador/periférico. **Control:** Bits que indican al controlador/periférico realizar determinada acción.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 33

---

### Q: ¿Qué son los bridges en la arquitectura de E/S de un PC?

**A:** Son dispositivos que interconectan diferentes buses del sistema. Por ejemplo, el System Controller (Northbridge) conecta CPU, AGP y memoria, mientras el Peripheral Bus Controller (Southbridge) conecta PCI, LAN, SCSI y otros buses.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 33

---

## Tema 6: Interrupciones

### Q: ¿Qué es una interrupción?

**A:** Es un mecanismo que provoca la alteración del orden lógico de ejecución de instrucciones como respuesta a un evento externo, generado por el hardware de E/S en forma asincrónica al programa que está siendo ejecutado.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 33

---

### Q: ¿Cómo se genera un pedido de interrupción?

**A:** Los controladores de E/S disponen de una señal de salida INT que toma el valor 1 cuando el controlador interrumpe. La CPU tiene una entrada INT que consulta para saber si hay pedido de interrupción.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 34

---

### Q: ¿Qué diferencia hay entre detección por nivel y por flanco?

**A:** **Por nivel:** La CPU reconocerá que hay pedido de interrupción mientras INT valga 1. **Por flanco:** La CPU reconocerá el pedido por el flanco ascendente de INT (transición de 0 a 1).

**Source:** Resumen Práctico Completo Arqui.pdf, Página 34

---

### Q: ¿Cuáles son los pasos del proceso de interrupción?

**A:** 1) "Termina" la instrucción actual, 2) Guarda el IP para continuar después, 3) Identifica el controlador que interrumpió, 4) Obtiene la dirección de la rutina de servicio del vector de interrupciones, 5) Enmascara nuevas interrupciones, 6) Ejecuta la rutina de servicio.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 34

---

### Q: ¿Qué es el mecanismo INT/INTA?

**A:** La CPU dispone de una única entrada INT a la cual se conectan en OR todos los pedidos de interrupción. INTA (Interrupt Acknowledge) es la señal de respuesta de la CPU confirmando que procesará la interrupción.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 35

---

### Q: ¿Qué es un controlador de interrupciones?

**A:** Es un dispositivo que gestiona múltiples fuentes de interrupción. Genera el pedido a la CPU a través de INT y devuelve por INTA la decisión tomada sobre cuál interrupción atender, implementando esquemas de prioridad.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 35

---

### Q: ¿Cómo funciona la identificación de interrupción por software?

**A:** Aplica cuando hay múltiples controladores conectados en OR a INT. La rutina de servicio recorre los controladores leyendo sus registros de estado hasta encontrar el que tiene su bit de pedido de interrupción en 1, luego invoca la subrutina específica.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 35

---

### Q: ¿Qué es el enmascaramiento de interrupciones?

**A:** La CPU inhibe la aceptación de todas las solicitudes de interrupción. Es el estado inicial y puede usarse para secciones críticas del código que no deben ser interrumpidas.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 35

---

### Q: ¿Qué es la deshabilitación de interrupciones?

**A:** La CPU actúa individualmente sobre cada controlador para inhibir su eventual pedido de interrupción. Permite control más fino que el enmascaramiento global.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 35

---

### Q: ¿Qué tipos de prioridad existen para interrupciones?

**A:** **Prioridad fija:** Se atiende en orden jerárquico predeterminado. **Prioridad configurable:** Cambia en función de las condiciones del sistema. **Sin prioridad:** Sistema de selección sin jerarquía definida.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 35

---

### Q: ¿Qué son las interrupciones simultáneas?

**A:** Ocurren cuando múltiples dispositivos interrumpen al mismo tiempo. Se resuelve adoptando una estrategia de prioridades para determinar cuál se atiende primero.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 36

---

### Q: ¿Qué es la interrupción de interrupción?

**A:** Ocurre cuando llega una solicitud de interrupción mientras se está procesando otra. La atención o no de la nueva solicitud dependerá del esquema de jerarquía/prioridades implementado.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 36

---

### Q: ¿Qué son las rutinas de interrupción?

**A:** Son piezas de código que se ejecutan como resultado del mecanismo que desencadena la CPU al procesar un pedido de interrupción. Deben preservar el contexto (registros, estado) para no afectar el programa interrumpido.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 36

---

### Q: ¿Qué diferencia hay entre máquina dedicada y no dedicada para interrupciones?

**A:** **No dedicada:** Múltiples programas ejecutándose, programados por distintos equipos sin coordinación; debe preservar todo el contexto. **Dedicada:** Completamente dedicada a una función, todos los programas coordinados; puede optimizar preservación de contexto.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 36

---

### Q: ¿Cuáles son las estrategias de programación con interrupciones?

**A:** 1) Toda la lógica en el programa principal, rutinas solo modifican banderas. 2) Toda la lógica en las rutinas, programa principal en loop o solo inicializa. 3) Lógica distribuida entre programa principal y rutinas.

**Source:** Resumen Práctico Completo Arqui.pdf, Página 36

---

