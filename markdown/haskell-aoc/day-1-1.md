# An AoC Intro to Haskell - Day 1, Part 1

## Last updated 2020-04-10

[Back to AoC Intro to Haskell Index](./)

## Intro

[Day1, Part1][1] is *very* straightforward. We need to calculate the total fuel requirement to
launch a series of modules, where the requirement for one module is:

    fuel = max(mass // 3 - 2, 0)

Where `mass` is the mass of the module and `//` is floor division (rounding down). We take the `max`
of the result versus zero to ensure we don't get a negative fuel value.

The best we can do here is O(n), as we need to do the calculation of each module. The input is the
module weights, line-separated:

    104451
    112406
    109733
    ...
    
## Iterative Approach

A naive iterative approach, using Python 3 as an example, assuming our input has already been read
into an array of integers called `ipt` (`input` is a builtin func in Python 3):

    total = 0
    
    for i in ipt:
        total += max(i // 3 - 2, 0)

## Functional (Python) Approach

We can convert the above to a semi-functional approach while still using Python. This will help
inform our pure functional Haskell solution:

    total = sum(map(lambda i: max(i // 3 - 2, 0), ipt))

I've used `map` here instead of a list comprehension because `map` returns a generator while a list
comprehension produces a list. Not a huge performance gain, but the laziness better simulates
Haskell (more on that later).

## Haskell: Reading in the File

The first thing I'm going to do is make the problem more complicated than it is treated above. File
I/O in Python is old hat, so I omitted it, but I/O in Haskell is *interesting*. This is because
Haskell is pure, and I/O is decidedly not.

Practically, Haskell functions are separated into pure and impure. Pure ones are ones that are
mathematical, deterministic, don't have side-effects, and *always return something* (technically
only the side-effects part is necessary though). Having these properties is fantastic from a
programming perspective, as it allows all sorts of great assumptions about correctness and
optimizations.

Impure functions are ones that have side-effects, can break, are possibly nondeterministic. I/O
falls into this category. Therefore, any function in Haskell that uses I/O is automatically impure.
If a function calls an impure function, it also becomes impure. The impurity "spreads", so it
encourages the programmer to keep their impure functions separate from their pure functions as much
as possible.

Every Haskell program has a `main` function, which is decidedly impure, as, at the very first, it
reads arguments from standard input.

Enough manifesto – let's read a file:

    main = do
        rawInput <- readFile "input.txt" -- Read input file to String

In main, we want to do three things:

 1. Read the input file (above)
 1. Parse it to a list of integer module weights
 1. Calculate the sum of the fuel values for those integers
 
We use the `do` keyword because we want to do multiple things in which the order is important.

The above accomplishes step 1. [`readFile`][2] has the function signature `FilePath -> IO String`.
The `IO` part of `IO String` tells us that this is an "I/O monad" containing a `String`. We can talk
more about monads later, but in this case, simply think of it as a wrapper that may contain a
`String` or may contain an `IOError`. Functions are called by simply listing the name, then the
arguments space-separated: `myFunc arg1 arg2 arg3`.

`<-` optimistically unwraps the `IO String` to get at the `String` underneath, then binds it to the
variable `rawInput`. If there was an I/O error, this is where it would crash.

Anything that starts with `--` is a comment.

So now we have a variable bound to a `String`, which contains our entire input file (we don't
*really* have this, on account of laziness, but shush for now).

## Haskell: Parsing the String

Time for step 2 – we need to turn our `String` into a list of integers.

*(Warning: I'm going to be doing the rest of this in a very obtuse way all within the `main`
function. This is because I can illustrate the most concepts that way in the smallest amount of
space.)*

Let's (proactive pun) add another line to our `main`:

    main = do
        rawInput <- readFile "input.txt"
        -- Parse the String to a list of Ints
        let input = [read i :: Int | i <- lines rawInput] in
            -- TODO
            
Looks weird, yeah? Here's the breakdown:

`lines` is a function with a signature `String -> [String]`. That is, it takes a `String` and
produces a list of `Strings` by splitting the original `String` on newline characters.

Constructs of the form `[myFunc x | x <- myList]` are [list comprehensions][3]. Just like Python's
comprehension, it takes a list to the right of the `<-` and an operation to the left of the `|` and
applies the operation to each list item (bound to `x`) to produce a new list (just like `map`). The
above in Python would look like `[myFunc(x) for x in myList]`.

In the Python 3 version of this, I used `map` to attempt laziness via a Python generator. In
Haskell, pretty much everything is lazy by default, and this applies to list comprehension.

`read i :: Int` is a typecast, in a way. `read` is a funny Haskell function with the signature
`Read a => String -> a` which means "given a type, `a` that is part of the `Read` typeclass (can be
parsed), attempt to parse the given `String` to that type." Wordy, but more simply, "try to parse
this `String` to an `Int`" in this concrete case.

So, overall, `let input = [read i :: Int | i <- lines rawInput]` is a one-liner that splits our raw
input into lines, parses each line to an `Int`, then binds that list of `Ints` to the variable
`input`.

Why does this binding use `let` instead of `<-` like the `readFile` one? Because this operation is
(theoretically) pure – there's no `IO Monad` involved. [Let bindings][4] contextually bind a value
to a variable name for the scope of their body (the `in` block).

## Haskell: Finishing the Calculation

All that's left now is to perform the actual calculation, which we'll do in the `let ... in` body
using, you guess it, a list comprehension.

Our final program (less the comments) is below:

    main = do
        rawInput <- readFile "input.txt"
        let input = [read i :: Int | i <- lines rawInput] in
            -- Perform the calculation and print result
            print $ sum [max 0 $ quot i 3 - 2 | i <- input]

Your first question is probably "`$`???", and we'll get to that.

The list comprehension is the same as before, except we aren't doing any extra work on the right
side of it, as we already have the input list we want.

The operation is `max 0 $ quot i 3 - 2`, which is a mouthful. `quot` is a function with signature
`a -> a -> a` that performs integer division, truncated towards zero (rounded down). This signature
looks weird, and that's because Haskell functions only actually take a single argument. Ever. At
least, that's how it's abstracted. So how can division occur, as obviously division requires two
arguments? Simple: when given the first argument, `quot` returns a **curried** function with
signature `a -> a`, which the second argument is given to. You'll get used to it.

`quot i 3` takes `i` and divides it by 3, rounding down. Function application has really high
precedence in Haskell, so the `quot i 3 - 2` can be read as `((quot i) 3) - 2)` in a kind of
pseudo-Polish Notation, or `quot(i)(3) - 2` in a curried-function notation, or `quot(i, 3) - 2` in a
more familiar C-style notation.

Now we can talk about `max 0 $ quot i 3 - 2`. `max` is a function with signature
`Ord a => a -> a -> a` – it consumes two arguments of the same type, `a`, that are of Typeclass
`Ord`erable, and returns the maximum of the two. The `$` is [actually a function][5] (gasp! though
it's probably actually a kind of macro) with the signature `(a -> b) -> a -> b`. It's an **infix**
function, meaning it's first and second arguments are on either side of it. On the left, a function
that takes an `a` and returns a `b` (note: these can be the same type, they just aren't guaranteed
to be). `max 0` fits this bill, as `max`, with one argument applied, returns an `(a -> a)`. `$` then
takes its right argument and applies it to the left argument.

Why do all this work though? The main reason is code cleanliness. Without the `$`, `max 0 quot i 3`
(I'm omitting the `- 2` for brevity) would be interpreted as `((max 0 quot) i 3)`, as function
application has very high precedence. `$` evaluates its right argument first, *then* applies it to
it's left argument, so `max 0 $ quot i 3` is instead interpreted `(max 0) (quot i 3)`, which could
also be thought of as `(max 0 (quot i 3))`. Mentally, when you see a `$`, it's the same as replacing
`$` with a `(` and adding a `)` at the end of the line. `max 0 $ quot i 3` becomes
`max 0 (quot i 3)`.

After our list comprehension is done, we have a list of all the fuel weights, and we apply that to
`sum`, a function with signature `(Foldable t, Num a) => t a -> a`. Foldables are anything that can
be "folded" into a single value, and Nums are numbers (obviously). `sum` folds our list into a
single value by accumulating each element with `+`.

`print` has the signature `Show a => a -> IO ()`. Typeclass Show includes any type that has a way to
be displayed as a String. `IO ()` is an I/O Monad that doesn't contain anything. This is used
because writing to standard out can still error, but if it succeeds, we don't expect a value back.
We use `$` again so that `print` doesn't just try to `(print sum) ...`, which would be pretty
useless.

## Haskell: Final Program

I can confirm that our final program:

    main = do
        rawInput <- readFile "input.txt"
        let input = [read i :: Int | i <- lines rawInput] in
            print $ sum [max 0 $ quot i 3 - 2 | i <- input]

Nets me the correct solution for Day 1, Part 1. It's not pretty, but that wasn't the point.
Obviously this could be refactored to use separate functions, and `map` could be used instead of
list comprehensions if you like that style.

    $ runhaskell day-1-1.hs
    3538016
    
Eventually, [Day 1, Part 2](./day-1-2.html) will adapt this code further, and introduce a little
recursion for funsies.

— Mitch

   [1]: https://adventofcode.com/2019/day/1 "Advent of Code 2019, Day 1"
   [2]: https://hackage.haskell.org/package/base-4.12.0.0/docs/Prelude.html#v:readFile "Haskell readFile documentation"
   [3]: https://learnyouahaskell.com/starting-out#im-a-list-comprehension "Learn You a Haskell: list comprehensions"
   [4]: https://learnyouahaskell.com/syntax-in-functions#let-it-be "Learn You a Haskell: let bindings"
   [5]: http://learnyouahaskell.com/higher-order-functions#function-application "Learn You a Haskell: function application"
