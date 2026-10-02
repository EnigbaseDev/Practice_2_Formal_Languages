# Practice_2_Formal_Languages

# NFA to DFA Determinization Engine (Subset Construction)

Automated system for determinizing **Nondeterministic Finite Automata (NFA)** into equivalent **Deterministic Finite Automata (DFA)** implementing the classical Subset Construction paradigm formulated by Dexter C. Kozen (*Automata and Computability*, 1997, Lecture 6).

Submission assignment for **SI2002 — Formal Languages**, Universidad EAFIT.

---

## 1. Academic Credentials

| Field | Detail |
| :--- | :--- |
| **Authors** | Daniel Serna & Carlos Monsalve |
| **Course ID** | SI2002 |
| **Course Title** | Formal Languages |
| **Faculty Instructor** | Prof. Oscar Rodriguez Cifuentes |
| **Academic Unit** | Department of Computer Science, Universidad EAFIT |
| **Academic Period** | 2026-2 (September 2026) |

---

## 2. Technical Environment & Dependencies

This software is developed strictly within the boundaries of the **Python Standard Library**. It requires zero external package installations, no virtual environment setups, and no build dependencies.

* **Target Runtimes**: Python 3.10 through 3.14
* **Operating Systems Verified**: Linux (Ubuntu 22.04+ LTS, Debian 12), Windows 10/11 x64, macOS 13+
* **Standard Modules**: `sys`, `re`, `math`, `html`, `json`, `collections` (`deque`), `pathlib` (`Path`), `dataclasses`, `typing`
* **Development IDE**: Visual Studio Code / Terminal Shell

---

## 3. Project File Tree

```
├── conversor_afn_afd.py   # Core object-oriented engine, parser and SVG/HTML generator
├── README.md              # Academic documentation in English (official delivery file)
├── ejecutar.py            # Quick-run script for VS Code execution
├── run.py                 # Convenience alias for executing with one click
├── input.txt              # Standard benchmark input file containing the assignment case
└── output.html            # Stand-alone interactive HTML report with SVG diagrams
```

---

## 4. Execution Guide

The program is engineered to process automata from **standard input (`sys.stdin`)** and write exclusively to **standard output (`sys.stdout`)**, complying strictly with the non-negotiable grading rule: *"Do not print extra lines"*.

### 4.1 Pure Console Execution (Input Redirection)

#### Windows — Command Prompt (CMD)
```cmd
python conversor_afn_afd.py < input.txt
```

#### Windows — PowerShell
```powershell
Get-Content input.txt | python conversor_afn_afd.py
```

#### Linux / macOS — Bash or Zsh
```bash
python3 conversor_afn_afd.py < input.txt
```

---

### 4.2 Interactive Web Report Generation (Optional Feature)

To produce an interactive visual document containing SVG diagrams and a live string simulation workbench, supply the `--html [filename]` argument:

#### Windows (CMD)
```cmd
python conversor_afn_afd.py --html output.html < input.txt
```

#### Windows (PowerShell)
```powershell
Get-Content input.txt | python conversor_afn_afd.py --html output.html
```

#### Linux / macOS
```bash
python3 conversor_afn_afd.py --html output.html < input.txt
```

Double-click `output.html` or open it with any modern web browser to view the interactive diagrams.

---

### 4.3 Direct VS Code Execution (▶ Run Button)

To run the program without managing terminal input redirection manually:
1. Open [`ejecutar.py`]("File directory/"ejecutar.py) (or `run.py`) in VS Code.
2. Click the **▶ (Run Python File)** button in the top right.
3. It will pipe `input.txt`, print the exact DFA matrix into the console, and generate `output.html`.

---

## 5. Input and Output Specification

### 5.1 Input File Grammar

The input consists of plain ASCII text formatted as follows:

```text
c                   [Number of automaton cases, c > 0]
n                   [State cardinality |Q|, states are 1, 2, ..., n]
S                   [Space-delimited initial states]
a b ...             [Space-delimited alphabet symbols from {a-z}]
F                   [Space-delimited accepting states, or 0 if empty]
1 row_1             [Transition row for state 1]
...
n row_n             [Transition row for state n]
```

* `0` denotes the empty set $\emptyset$.
* Transition cells contain either `0` or explicit sets enclosed in curly braces (e.g. `{1 5}`).

---

### 5.2 Console Output Grammar

For each input automaton, the engine prints a cleanly aligned transition matrix:
* **Row 1**: Column headers corresponding to the alphabet symbols.
* **Subsequent Rows**: Each reachable DFA macro-state.
  * `->` indicates the start macro-state.
  * `<-` designates an accepting macro-state.
  * `-><-` marks a macro-state that is both initial and accepting.
  * Trap/sink states are rendered as `0`.
  * The order of rows strictly follows the **Breadth-First Search (BFS) discovery sequence**.
* **Zero extraneous lines** are printed to ensure absolute compatibility with automated diff testing.

#### Benchmark Output:
```text
             a         b
-> {3 5}     {1 2 4 5} {4}
<- {1 2 4 5} {1 5}     {4 5}
<- {4}       0         {5}
<- {1 5}     {1 5}     {4}
<- {4 5}     {1 5}     {4 5}
   0         0         0
   {5}       {1 5}     {4}
```

---

## 6. Algorithmic Mechanics: Subset Construction

### 6.1 Formalization

Given an input NFA defined as a 5-tuple:
$$N = (Q, \Sigma, \Delta, S, F)$$
where:
* $Q = \{1, 2, \dots, n\}$ is the set of states.
* $\Sigma$ is the alphabet of lowercase symbols.
* $\Delta: Q \times \Sigma \to \mathcal{P}(Q)$ is the nondeterministic transition function.
* $S \subseteq Q$ is the set of initial states.
* $F \subseteq Q$ is the set of accepting states.

The algorithm builds an equivalent DFA:
$$M = (Q_D, \Sigma, \delta_D, s_0, F_D)$$
defined by:

1. **Initial Macro-State ($s_0$):**
   $$s_0 = S$$

2. **Transition Function ($\delta_D$):**
   For any macro-state $A \subseteq Q$ and symbol $a \in \Sigma$:
   $$\delta_D(A, a) = \bigcup_{q \in A} \Delta(q, a)$$
   If $A = \emptyset$, $\delta_D(\emptyset, a) = \emptyset$ (absorbing dead/trap state).

3. **Reachable State Exploration:**
   Rather than instantiating the complete theoretical power set of size $2^{|Q|}$, states are explored lazily via a FIFO queue initialized with $s_0$. A transition is computed for each alphabet symbol; newly uncovered sets are registered and appended to the queue until the exploration queue is exhausted.

4. **Accepting Macro-States ($F_D$):**
   $$F_D = \{ A \in Q_D \mid A \cap F \neq \emptyset \}$$

---


## 7. Optional Features: SVG Diagram & Live Evaluator

Under Section 4.5 of the assignment specifications (*"Optional: You might include additional features to your implementation, for instance, to print automata as diagrams"*), generating `--html output.html` provides:

1. **Pill-Based SVG Automaton Diagram**:
   * Nodes rendered as styled rounded pills (`<rect rx="...">`), double-bordered for accepting states, and dashed for the empty state $\emptyset$.
   * Smooth cubic Bézier flow curves between hierarchical levels and top circular arcs (`<path d="M... A...">`) for self-loops.
2. **Real-Time Client-Side String Simulator**:
   * Interactive input bar allowing users to enter arbitrary words over $\Sigma$.
   * Displays the transition trajectory step-by-step:
     $$s_0 \xrightarrow{a} S_1 \xrightarrow{b} S_2 \dots$$
   * Produces an immediate verdict: `ACCEPTED` or `REJECTED`.
   * **Animates and highlights the active state** directly inside the SVG graph.

---

## 8. References

* **Kozen, Dexter C.** (1997). *Automata and Computability*. 1st ed. Berlin, Heidelberg: Springer-Verlag.
