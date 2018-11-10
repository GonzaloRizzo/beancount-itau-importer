import re
from datetime import datetime
from io import StringIO

from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams


def pdf_to_text(filepath):
    output = StringIO()
    with open(filepath, 'rb') as pdf_file:
        extract_text_to_fp(pdf_file, output, laparams=LAParams())
    return output.getvalue()


DateExp = r'''
    (\d{2}) \s (\d{2}) \s (\d{2})
'''

CardEndingExp = r'''
  \d{4}
'''

PayTokenExp = r'''
  PAGOS
'''

DescriptionFieldExp = r'''
  [^\s]   # Start by matching a non whitespace character
  .+?     # Lazely matches as few characters as possible
  (?=\s)  # Makes sure that there's at least a whitespace after the characters
'''

PaymentNumberExp = r'''
  (\d+)  # More than one digit
  \s*  # Optional Space
  \/   # / Separator
  \s*  # Optional Space
  (\d+)  # More than one digit
'''

AmountExp = r'''
-?       # Optional negative sign
[\d\.]+  # Dot formatted number
\,       # Comma
\d{2}    # Decimal numbers
'''

SpacerExp = r'''
  \s{13}
'''

RecordExp = rf'''
^

\s* # Might start with whitespace

(?P<date>{DateExp}) \s+ # Transaction date with mandatory space at the end


  (?P<pay_token>{PayTokenExp})?

  (?P<card_ending>{CardEndingExp})?


\s*

(?P<description>{DescriptionFieldExp})?
\s*
(?P<payment_number>{PaymentNumberExp})?

\s*
(?:
  (?P<amount_origin>{AmountExp})
|
  {SpacerExp}
)

\s*
(?:
  (?P<amount_uyu>{AmountExp})
|
  {SpacerExp}
)

\s*
(?:
  (?P<amount_usd>{AmountExp})
|
  {SpacerExp}
)

$
'''


def parse_amount(text):
    if not text:
        return None
    return float(text.replace('.', '').replace(',', '.'))


def parse_payment_number(payment_number):
    if not payment_number:
        return None
    current, total = re.match(PaymentNumberExp, payment_number, re.X).groups()
    return {
        'current': current,
        'total': total,
    }


def credit_card_parser(filename):
    text = pdf_to_text(filename)
    lines = text.splitlines()
    entries = []
    for line in lines:
        match = re.match(RecordExp, line.ljust(120), re.X)

        if not match:
            continue

        match_dict = match.groupdict()
        entries.append({
            'date': datetime.strptime(match_dict['date'], '%d %m %y').strftime('%Y-%m-%d'),
            'description': match_dict['description'],
            'is_card_payment': bool(match_dict['pay_token']),
            'card_ending': match_dict['card_ending'],
            'payment_number': parse_payment_number(match_dict['payment_number']),
            'amount_usd': parse_amount(match_dict['amount_usd']),
            'amount_uyu': parse_amount(match_dict['amount_uyu']),
            'amount_origin': parse_amount(match_dict['amount_origin']),
        })

    return entries
