async function loadExpenses() {
  const res = await fetch("/api/expenses");
  const data = await res.json();

  console.log(data); // render UI here
}

async function addExpense() {
  await fetch("/api/add", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      amount: 100,
      category: "Food",
      note: "Test",
      date: "2026-04-18"
    })
  });

  loadExpenses();
}

loadExpenses();