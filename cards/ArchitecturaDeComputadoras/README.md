# Flashcards: Arquitectura de Computadoras

## Summary

**Generated:** October 16, 2025
**Course:** Arquitectura de Computadoras (Computer Architecture)
**Total Flashcards:** 158
**Document Source:** Resumen Práctico Completo Arqui.pdf (36 pages)
**Format:** JSON (flashcards.json)

---

## Documents Processed

1. **Resumen Práctico Completo Arqui.pdf**
   - Author: Diego González (2007)
   - Pages: 36
   - Type: Practical summary/study guide
   - Language: Spanish

---

## Flashcard Distribution by Topic

| Topic | Number of Cards | Page Range |
|-------|----------------|------------|
| Representaciones de Datos - Sistemas de Codificación | 5 | 2 |
| Detección y Corrección de Errores | 6 | 2-3 |
| Representación Interna de Datos | 12 | 3-4 |
| Álgebra de Boole - Axiomas y Propiedades | 12 | 5 |
| Álgebra de Boole - Modelos | 6 | 5-6 |
| Funciones Booleanas | 6 | 6-7 |
| Circuitos Combinatorios - Compuertas | 3 | 8 |
| Bloques Constructivos | 11 | 9-14 |
| Circuitos Secuenciales - Flip-Flops | 13 | 15-20 |
| Modelación y Diseño de Circuitos Secuenciales | 2 | 21 |
| Máquinas de Estado | 9 | 24-25 |
| Arquitectura de Von Neumann | 4 | 26 |
| CPU - Componentes | 6 | 26-27 |
| Ciclo de Instrucción | 4 | 27 |
| Registros de la CPU | 6 | 28 |
| Unidad de Control | 2 | 30 |
| Entrada/Salida - Buses | 10 | 30-31 |
| Periféricos y Controladores | 9 | 31-33 |
| Interrupciones | 15 | 33-36 |

**Total:** 144 cards distributed across 19 subtopics within 8 major themes

---

## Topics Covered

### 1. Representaciones de Datos
- **Sistemas de codificación:** Bits, bytes, códigos binarios, distancia entre códigos
- **Detección y corrección de errores:** Paridad, códigos de Hamming, CRC
- **Representación interna:** Caracteres (ISO 10646, UNICODE), strings, enteros sin signo
- **Enteros con signo:** Valor absoluto y signo, desplazamiento, complemento a uno/dos
- **Decimales:** Empaquetado, punto flotante (IEEE 754), normalizado vs denormalizado

### 2. Álgebra de Boole
- **Axiomas:** Conjunto G, reglas de combinación, neutros, conmutatividad, distributividad, complemento
- **Propiedades:** Dualidad, asociatividad, idempotencia, neutros cruzados, doble complemento, De Morgan
- **Modelos:** Lógico (V, F), circuital (A, C), binario (0, 1)
- **Conectivas:** OR, AND, NOT, NAND, NOR, XOR, IGUAL
- **Funciones booleanas:** Definición por extensión/comprensión, tabla de verdad
- **Simplificación:** Método algebraico, Mapas de Karnaugh (3-5 variables)

### 3. Circuitos Combinatorios
- **Compuertas lógicas:** NOT, AND, OR, NAND, NOR, XOR
- **Bloques lógicos:** Representación compacta de circuitos complejos
- **Decodificador:** N entradas → 2^N salidas
- **Multiplexor:** N + 2^N entradas → 1 salida (selector de datos)
- **Demultiplexor:** Inverso del multiplexor
- **Sumador completo:** 1 bit y N bits en cascada
- **ROM:** Memoria de solo lectura, estructura interna
- **Retardo de conmutación:** Tiempo de propagación, solución con relojes
- **Lógica tri-state:** Estados 0, 1, Z (alta impedancia)

### 4. Circuitos Secuenciales
- **Definición:** Salida depende de entradas actuales y anteriores
- **Flip-flops:** Elementos de memoria básicos
  - R-S (asincrónico/sincrónico)
  - D (dato, ecuación: Qn+1 = D)
  - T (toggle, ecuación: Qn+1 = Q̄nT + QnT̄)
  - J-K (universal, ecuación: Qn+1 = JQ̄n + K̄Qn)
- **Control:** Sincrónico (señal G), asincrónico (cambio inmediato)
- **Control por flanco:** Actualización en transiciones
- **Entradas especiales:** Set/Clear (asincrónicas), Clock Enabled (CE)
- **Contadores:** Regresivos y progresivos con flip-flops T y D
- **Modelación:** Y = G(X, E), E' = H(X, E) (Mealy)
- **Diseño:** 7 pasos desde AFD hasta circuito final

### 5. Máquinas de Estado
- **Estados:** Clases de equivalencia de secuencias entrada-salida
- **AFD:** Autómata Finito Determinista - M = (E, e0, Σ, δ)
- **Máquina de Mealy:** Salida asociada a transición - λ: E × Σ → Δ
- **Máquina de Moore:** Salida asociada a estado - λ: E → Δ
- **Máquina lógica general:** Puede resolver problemas computables
- **Diseño general:** ROM + RAM para estados
- **Máquina programable:** RAM en lugar de ROM

### 6. Computadora - Arquitectura de Von Neumann
- **Concepto:** Programa almacenado, secuencia ordenada de instrucciones
- **Bloques:** CPU (ejecuta), MEM (almacena), E/S (comunica)
- **Variantes:** Set de instrucciones, formato, registros, direccionamiento, E/S, interrupciones
- **ALU:** Operaciones aritméticas, lógicas, desplazamiento
- **UC:** Implementa ciclo de instrucción
- **Banco de registros:** Memoria interna de alta velocidad
  - Totalmente visibles (operandos/direcciones)
  - Parcialmente visibles (IP, PC, SP, PS, FLAGS)
  - Internos (constantes, estado UC, IR, MAR, MDR)

### 7. Ciclo de Instrucción
- **Fetch:** Leer instrucción desde memoria (usa IP)
- **Decode:** Analizar código binario de la instrucción
- **Read:** Acceder a memoria para obtener operandos
- **Execute:** Ejecutar operación en ALU
- **Write:** Escribir resultado en destino
- **Registros clave:**
  - IP/PC: Puntero de instrucción
  - SP: Puntero de pila (LIFO)
  - PS: Estado del procesador (FLAGS)
  - IR: Instrucción actual
  - MAR: Dirección de memoria en el bus
  - MDR: Dato a leer/escribir en memoria

### 8. Unidad de Control
- **Lógica cableada:** Máquina de Mealy con diagrama de estados
- **Lógica microprogramada:** Microprogramas con microinstrucciones
- **Microprogramación vertical:** Bits codificados de señales de control
- **Microprogramación horizontal:** Bits de control sin codificar

### 9. Entrada/Salida
- **Bus:** Agrupación de líneas (Dirección, Datos, Control)
- **Bus de direcciones:** Transporta direcciones de memoria/E/S
- **Bus de datos:** Transporta información transferida
- **Bus de control:** Señales (Memory_R/W, I/O_R/W, Bus_Request/Grant, Transfer_ACK, Interrupt_R/ACK, Clock, Reset)
- **Bus simple (Master-Slave):** CPU controla
- **Bus inteligente:** Arbitraje para determinar Master
- **Arbitraje centralizado:** Entidad con mayor jerarquía controla
- **Arbitraje distribuido:** Inteligencia distribuida
- **Buses internos/externos:** Dentro/fuera de la frontera del sistema

### 10. Periféricos y Controladores
- **Periféricos:** Vínculo con el mundo exterior
- **Controlador:** Inteligencia del periférico, maneja comunicación
- **Ubicaciones:** Gabinete del computador, del periférico, distribuido
- **Acceso:** E/S mapeada en puertos vs mapeada en memoria
- **Registros:**
  - Solo lectura (estado, datos de entrada)
  - Solo escritura (comandos, datos de salida)
  - Lectura/Escritura independiente
  - Tipos: Entrada, Salida, Estado, Control
- **Bridges:** Interconexión de buses (Northbridge, Southbridge)

### 11. Interrupciones
- **Definición:** Alteración asincrónica del orden de ejecución
- **Generación:** Señal INT de controlador → Entrada INT de CPU
- **Detección:** Por nivel (mientras INT=1) vs por flanco (0→1)
- **Proceso:** Terminar instrucción, guardar IP, identificar controlador, obtener dirección de rutina, enmascarar, ejecutar
- **Mecanismo INT/INTA:** Pedido y confirmación
- **Identificación:**
  - Hardware: Líneas independientes, INT/INTA, controlador de interrupciones
  - Software: Rutina recorre controladores
- **Habilitación:** Enmascaramiento (global), deshabilitación (individual)
- **Prioridades:** Fija, configurable, sin prioridad
- **Superposición:** Simultáneas, interrupción de interrupción
- **Rutinas:** Preservación de contexto
- **Estrategias:** Máquina dedicada vs no dedicada
- **Programación:** Lógica en principal, en rutinas, o distribuida

---

## JSON Format Structure

The flashcards are stored in JSON format with the following schema:

```json
{
  "course": "Arquitectura de Computadoras",
  "totalCards": 158,
  "sources": ["Resumen Práctico Completo Arqui.pdf"],
  "topics": [
    {
      "name": "Topic Name",
      "cards": [
        {
          "id": 1,
          "question": "Question text",
          "answer": "Answer text",
          "source": "Document, Page X"
        }
      ]
    }
  ],
  "additionalNotes": {
    "documentSummary": "Overview",
    "studyTips": ["Tip 1", "Tip 2"]
  }
}
```

---

## Example Flashcards

### Data Representation
**Q:** ¿Cómo funciona la representación en complemento a dos?
**A:** Representa los números por complemento a uno y luego le suma 1. Permite representar -2^(n-1) a 2^(n-1) - 1. Tiene una única representación para el cero y las operaciones coinciden con lo representado.
**Source:** Resumen Práctico Completo Arqui.pdf, Página 3

### Boolean Algebra
**Q:** ¿Qué establece la Ley de De Morgan?
**A:** El complemento de una suma es el producto de los complementos, y viceversa: (a + b) negado = ā · b̄.
**Source:** Resumen Práctico Completo Arqui.pdf, Página 5

### Sequential Circuits
**Q:** ¿Cómo funciona un flip-flop J-K?
**A:** Funciona bajo flancos descendentes de reloj. Cuando J=0 y K=0 mantiene el estado, J=0 y K=1 pone Q=0, J=1 y K=0 pone Q=1, J=1 y K=1 invierte Q. Su ecuación característica es Qn+1 = JQ̄n + K̄Qn.
**Source:** Resumen Práctico Completo Arqui.pdf, Página 18

### CPU Architecture
**Q:** ¿Cuáles son las fases del ciclo de instrucción?
**A:** 1) Fetch: Leer la próxima instrucción de memoria, 2) Decode: Analizar el código binario, 3) Read: Acceder a memoria para operandos, 4) Execute: Ejecutar la operación en la ALU, 5) Write: Escribir el resultado en el destino.
**Source:** Resumen Práctico Completo Arqui.pdf, Página 27

### Interrupts
**Q:** ¿Cuáles son los pasos del proceso de interrupción?
**A:** 1) 'Termina' la instrucción actual, 2) Guarda el IP para continuar después, 3) Identifica el controlador que interrumpió, 4) Obtiene la dirección de la rutina de servicio del vector de interrupciones, 5) Enmascara nuevas interrupciones, 6) Ejecuta la rutina de servicio.
**Source:** Resumen Práctico Completo Arqui.pdf, Página 34

---

## Study Recommendations

1. **Sequential Study:** The topics build upon each other. Study in order:
   - Data Representation → Boolean Algebra → Combinatorial Circuits → Sequential Circuits → State Machines → Computer Architecture → I/O → Interrupts

2. **Key Concepts to Master:**
   - **Complement a dos:** Most common signed integer representation
   - **Hamming codes:** Error detection and correction mechanism
   - **Karnaugh maps:** Boolean function simplification
   - **Flip-flop types:** Understand R-S, D, T, J-K and their equations
   - **Mealy vs Moore:** Output timing differences
   - **Instruction cycle:** Fetch-Decode-Read-Execute-Write
   - **Interrupt handling:** INT/INTA mechanism and priorities

3. **Practice Problems:**
   - Convert numbers between different representations
   - Design Hamming codes for error correction
   - Simplify Boolean functions using Karnaugh maps
   - Design sequential circuits from state diagrams
   - Trace instruction execution through CPU registers
   - Simulate interrupt scenarios with priorities

4. **Hands-On Activities:**
   - Draw logic circuits from Boolean expressions
   - Build truth tables for complex functions
   - Design counters using different flip-flop types
   - Trace data flow through CPU during instruction execution
   - Model interrupt service routine execution

---

## File Structure

```
cards/ArchitecturaDeComputadoras/
├── README.md (this file - study guide)
├── flashcards.json (158 flashcards in JSON format)
└── flashcards.md (legacy markdown format - 158 flashcards)
```

---

## Notes

- All flashcards include precise source attribution with page numbers
- Concepts are explained in Spanish (original document language)
- Technical terms are preserved in their standard form
- Mathematical notation preserved: ⊕ (XOR), ∧ (AND), ∨ (OR), ¬ (NOT)
- Subscripts preserved: Qn+1, x^r, 2^n
- Circuit diagrams referenced but not embedded (see original PDF)
- JSON format uses plain text (no markdown formatting in values)
- Character escaping handled for special characters

---

## Usage in OpenDeck Application

These flashcards are designed for the OpenDeck Angular application:

1. **Import:** Load from `/cards/ArchitecturaDeComputadoras/flashcards.json`
2. **Parse:** Process JSON structure to extract Q&A pairs
3. **Display:** Show one card at a time with flip animation
4. **Topics:** Filter by 19 subtopics across 8 major themes
5. **Progress:** Track mastery per topic
6. **Search:** Filter by keyword or source page
7. **Source Navigation:** Link back to PDF page references
8. **Study Mode:** Sequential, random, or topic-focused
9. **Difficulty:** Mark cards for spaced repetition

---

## Additional Resources

For deeper understanding, complement these flashcards with:
- Original PDF document (diagrams and examples)
- Circuit simulation tools (Logisim, Digital)
- CPU simulators (SPIM, MARS for MIPS)
- Practice problems from textbooks
- Assembly language programming exercises

---

**Generated by:** OpenDeck v1.0
**AI Model:** Claude (Anthropic)
**Date:** 2025-10-16
**Format Version:** JSON Schema v1.0
