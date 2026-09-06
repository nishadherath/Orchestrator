# Support ticket 482

"I had a $200 cart and used a 10% off code. My total only dropped by $10, not
$20. Something is wrong with the discount."

Reproduce with:

    python3 -c "from checkout import total_with_discount; print(total_with_discount([200], 10))"
