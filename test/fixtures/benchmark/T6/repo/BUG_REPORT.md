# Support ticket 511

"I bought two items for $50 each and shipped to California, but my receipt
shows no sales tax at all. My total was just $100.00. Every other order
I've placed from California has had tax added."

Reproduce with:

    python3 -c "from cart import checkout; print(checkout([(50, 1), (50, 1)], 'ca'))"
