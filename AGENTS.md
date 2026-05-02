# Clean Code AI Agent Instructions

You are an AI coding agent. Produce code that is small, readable, testable, and easy to change.

## Core Rule

Prefer code that reads like a clear sequence of named actions.

A high-level function should describe the workflow by calling small, well-named functions in order.

```ts
async function completeCheckout(input: CheckoutInput): Promise<CheckoutResult> {
  const cart = await loadCart(input.cartId);
  const order = createOrder(cart, input.payment);
  await chargeCustomer(order);
  await sendReceipt(order);

  return toCheckoutResult(order);
}
```

## Function Design

- Keep functions small.
- Keep each function at one level of abstraction.
- Prefer descriptive function names over comments.
- Extract a function whenever a block needs explanation.
- Extract a function whenever a function mixes different abstraction levels.
- Avoid deeply nested logic.
- Return early to reduce indentation.
- Prefer pure functions when possible.
- Avoid hidden side effects.
- Pass only the data a function needs.
- Avoid long parameter lists.
- Use objects for related parameters.
- Avoid boolean flags that change function behavior.
- Split behavior into separate named functions instead.

## Preferred Structure

Write orchestration functions that call intention-revealing functions.

```ts
function registerUser(command: RegisterUserCommand): User {
  validateRegistration(command);
  const user = createUser(command);
  assignDefaultRole(user);
  publishUserRegistered(user);

  return user;
}
```

Each called function should do one focused thing.

```ts
function validateRegistration(command: RegisterUserCommand): void {
  ensureEmailIsValid(command.email);
  ensurePasswordIsStrong(command.password);
}
```

## Naming Rules

- Use names that explain intent.
- Prefer verbs for functions.
- Prefer nouns for values and objects.
- Avoid abbreviations unless they are standard in the project.
- Avoid vague names like `handle`, `process`, `data`, `item`, `temp`, and `stuff`.
- A function name should explain what the function does without requiring the reader to inspect its body.

## Abstraction Rules

Do not mix high-level business flow with low-level implementation details.

Bad:

```ts
function createInvoice(order: Order): Invoice {
  const total = order.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const invoice = { id: crypto.randomUUID(), total, createdAt: new Date() };
  database.invoices.insert(invoice);
  return invoice;
}
```

Better:

```ts
function createInvoice(order: Order): Invoice {
  const total = calculateOrderTotal(order);
  const invoice = buildInvoice(order, total);
  saveInvoice(invoice);

  return invoice;
}
```

## Comments

- Prefer better names and smaller functions over explanatory comments.
- Use comments only to explain why something exists, not what the code does.
- Delete comments that repeat the code.

## Error Handling

- Keep error handling explicit.
- Do not hide failures.
- Prefer domain-specific errors.
- Validate inputs at boundaries.
- Keep the happy path easy to read.

## Testing

- don't modify the tests
- after the refactoring is complete, run the tests to ensure they still pass
- if you add new functions, add tests for them.
- run tests in the venv envienoment with `pytest`

## Refactoring Checklist

Before finishing code, verify:

- No function is doing more than one job.
- High-level functions read like a sequence of named steps.
- Names are specific and intention-revealing.
- Complex expressions are extracted into named variables or functions.
- Duplicated logic is removed.
- Nesting is minimized.
- Side effects are isolated.
- Tests cover the important behavior.
- The code is simpler than when you started.
