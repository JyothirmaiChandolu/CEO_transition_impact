"""
Data Validation Module
Validates stock data for duplicates, primary keys, nulls, and data types
"""
import pandas as pd
import re
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Any


class DataValidator:
    """Validates stock data according to defined rules"""

    def __init__(self):
        self.validation_rules = {
            'date': {
                'can_null': False,
                'format': r'^\d{4}-\d{2}-\d{2}$',
                'dtype': 'string'
            },
            'ticker': {
                'can_null': False,
                'format': r'^[A-Z]{1,5}$',
                'dtype': 'string',
                'is_primary': True
            },
            'open': {
                'can_null': False,
                'dtype': 'float',
                'min': 0.01
            },
            'high': {
                'can_null': False,
                'dtype': 'float',
                'min': 0.01
            },
            'low': {
                'can_null': False,
                'dtype': 'float',
                'min': 0.01
            },
            'close': {
                'can_null': False,
                'dtype': 'float',
                'min': 0.01
            },
            'volume': {
                'can_null': False,
                'dtype': 'int',
                'min': 0
            }
        }

    def validate_dataframe(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """
        Validate dataframe and separate into valid and invalid rows

        Returns:
            Tuple of (valid_df, invalid_df, stats)
        """
        df = df.copy()
        valid_rows = []
        invalid_rows = []
        seen_keys = set()
        stats = {
            'total_rows': len(df),
            'valid_rows': 0,
            'invalid_rows': 0,
            'errors': []
        }

        for idx, row in df.iterrows():
            errors = []

            # Check primary key uniqueness (date + ticker)
            primary_key = f"{row.get('date')}_{row.get('ticker')}"
            if primary_key in seen_keys:
                errors.append(f"Duplicate primary key: {primary_key}")
            else:
                seen_keys.add(primary_key)

            # Validate each column
            for col, rule in self.validation_rules.items():
                if col not in row.index:
                    errors.append(f"Missing column: {col}")
                    continue

                val = row[col]

                # Null check
                if pd.isnull(val) or val == '':
                    if not rule.get('can_null', True):
                        errors.append(f"Null not allowed in {col}")
                    continue

                # Format check (regex)
                if 'format' in rule:
                    if not re.match(rule['format'], str(val)):
                        errors.append(f"Format mismatch in {col}: {val}")
                        continue

                # Type check
                expected_type = rule.get('dtype')
                try:
                    if expected_type == 'float':
                        float_val = float(val)
                        if rule.get('min') and float_val < rule.get('min'):
                            errors.append(f"{col} below minimum: {float_val}")
                    elif expected_type == 'int':
                        int_val = int(float(val))
                        if rule.get('min') and int_val < rule.get('min'):
                            errors.append(f"{col} below minimum: {int_val}")
                except (ValueError, TypeError):
                    errors.append(f"Type error in {col}: {val} (expected {expected_type})")

            if errors:
                invalid_rows.append({**row.to_dict(), '_errors': '; '.join(errors)})
                stats['errors'].extend(errors)
            else:
                valid_rows.append(row.to_dict())

        valid_df = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame()
        invalid_df = pd.DataFrame(invalid_rows) if invalid_rows else pd.DataFrame()

        stats['valid_rows'] = len(valid_df)
        stats['invalid_rows'] = len(invalid_df)

        return valid_df, invalid_df, stats

    def save_validation_results(self, valid_df: pd.DataFrame, invalid_df: pd.DataFrame,
                               ticker: str, output_dir: Path):
        """Save validated and invalid data to files"""
        output_dir = Path(output_dir)

        # Save valid data
        valid_dir = output_dir / 'stocks' / 'validated'
        valid_dir.mkdir(parents=True, exist_ok=True)
        valid_path = valid_dir / f'{ticker}_validated.json'
        valid_df.to_json(valid_path, orient='records', date_format='iso')

        # Save invalid data
        invalid_dir = output_dir / 'stocks' / 'invalid'
        invalid_dir.mkdir(parents=True, exist_ok=True)
        invalid_path = invalid_dir / f'{ticker}_invalid.csv'
        invalid_df.to_csv(invalid_path, index=False)

        return valid_path, invalid_path
