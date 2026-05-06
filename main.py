"""
Bank Account System
Консольное приложение для управления банковскими счетами
Автор: Алексей Смирнов
Версия: 1.0
"""

import json
import os
from datetime import datetime
from collections import deque
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from enum import Enum


# ==================== МОДЕЛИ (Model) ====================

class TransactionType(Enum):
    """Типы транзакций"""
    DEPOSIT = "пополнение"
    WITHDRAW = "снятие"
    TRANSFER = "перевод"
    INTEREST = "начисление процентов"
    FEE = "комиссия"


class Transaction:
    """Класс транзакции"""
    
    def __init__(self, transaction_type: TransactionType, amount: float, 
                 date: datetime = None, description: str = "",
                 from_account: str = "", to_account: str = ""):
        self.transaction_type = transaction_type
        self.amount = amount
        self.date = date or datetime.now()
        self.description = description
        self.from_account = from_account
        self.to_account = to_account
    
    def to_dict(self) -> dict:
        """Конвертация в словарь для JSON"""
        return {
            'transaction_type': self.transaction_type.value,
            'amount': self.amount,
            'date': self.date.isoformat(),
            'description': self.description,
            'from_account': self.from_account,
            'to_account': self.to_account
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Создание транзакции из словаря"""
        return cls(
            transaction_type=TransactionType(data['transaction_type']),
            amount=data['amount'],
            date=datetime.fromisoformat(data['date']),
            description=data['description'],
            from_account=data['from_account'],
            to_account=data['to_account']
        )
    
    def __str__(self):
        return (f"[{self.date.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"{self.transaction_type.value}: {self.amount:.2f}₽ - {self.description}")


class TransactionHistoryQueue:
    """Очередь истории транзакций"""
    
    def __init__(self, max_size: int = 100):
        self.queue = deque(maxlen=max_size)
    
    def add_transaction(self, transaction: Transaction) -> None:
        """Добавление транзакции в историю"""
        self.queue.append(transaction)
    
    def get_all_transactions(self) -> List[Transaction]:
        """Получение всех транзакций"""
        return list(self.queue)
    
    def get_transactions_by_type(self, transaction_type: TransactionType) -> List[Transaction]:
        """Фильтрация транзакций по типу"""
        return [t for t in self.queue if t.transaction_type == transaction_type]
    
    def get_transactions_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Transaction]:
        """Фильтрация транзакций по диапазону дат"""
        return [t for t in self.queue if start_date <= t.date <= end_date]
    
    def clear(self) -> None:
        """Очистка истории"""
        self.queue.clear()
    
    def __len__(self):
        return len(self.queue)


class Account(ABC):
    """Абстрактный базовый класс счета"""
    
    def __init__(self, account_number: str, owner_name: str, balance: float = 0.0):
        self._account_number = account_number
        self._owner_name = owner_name
        self._balance = balance
        self._transaction_history = TransactionHistoryQueue()
        self._is_active = True
    
    @property
    def account_number(self) -> str:
        return self._account_number
    
    @property
    def owner_name(self) -> str:
        return self._owner_name
    
    @property
    def balance(self) -> float:
        return self._balance
    
    @property
    def is_active(self) -> bool:
        return self._is_active
    
    def deposit(self, amount: float, description: str = "") -> bool:
        """Пополнение счета"""
        if not self._is_active:
            raise ValueError("Счет заблокирован")
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        
        self._balance += amount
        transaction = Transaction(
            TransactionType.DEPOSIT, amount, 
            description=f"Пополнение: {description}" if description else "Пополнение счета"
        )
        self._transaction_history.add_transaction(transaction)
        return True
    
    def withdraw(self, amount: float, description: str = "") -> bool:
        """Снятие средств со счета"""
        if not self._is_active:
            raise ValueError("Счет заблокирован")
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        if amount > self._balance:
            raise ValueError("Недостаточно средств")
        
        self._balance -= amount
        transaction = Transaction(
            TransactionType.WITHDRAW, amount,
            description=f"Снятие: {description}" if description else "Снятие средств"
        )
        self._transaction_history.add_transaction(transaction)
        return True
    
    def transfer_to(self, target_account: 'Account', amount: float, description: str = "") -> bool:
        """Перевод средств на другой счет"""
        if not self._is_active or not target_account._is_active:
            raise ValueError("Один из счетов заблокирован")
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        if amount > self._balance:
            raise ValueError("Недостаточно средств для перевода")
        
        # Снятие с текущего счета
        self._balance -= amount
        
        # Пополнение целевого счета
        target_account._balance += amount
        
        # Добавление транзакций в оба счета
        transaction_out = Transaction(
            TransactionType.TRANSFER, amount,
            description=f"Перевод на счет {target_account.account_number}: {description}" if description else f"Перевод на счет {target_account.account_number}",
            from_account=self._account_number,
            to_account=target_account.account_number
        )
        transaction_in = Transaction(
            TransactionType.TRANSFER, amount,
            description=f"Перевод со счета {self.account_number}: {description}" if description else f"Перевод со счета {self.account_number}",
            from_account=self._account_number,
            to_account=target_account.account_number
        )
        
        self._transaction_history.add_transaction(transaction_out)
        target_account._transaction_history.add_transaction(transaction_in)
        
        return True
    
    def get_transaction_history(self) -> List[Transaction]:
        """Получение истории транзакций"""
        return self._transaction_history.get_all_transactions()
    
    def filter_transactions_by_type(self, transaction_type: TransactionType) -> List[Transaction]:
        """Фильтрация транзакций по типу"""
        return self._transaction_history.get_transactions_by_type(transaction_type)
    
    def filter_transactions_by_date(self, start_date: datetime, end_date: datetime) -> List[Transaction]:
        """Фильтрация транзакций по дате"""
        return self._transaction_history.get_transactions_by_date_range(start_date, end_date)
    
    def deactivate(self) -> None:
        """Деактивация счета"""
        self._is_active = False
    
    def activate(self) -> None:
        """Активация счета"""
        self._is_active = True
    
    @abstractmethod
    def get_account_type(self) -> str:
        """Тип счета"""
        pass
    
    def to_dict(self) -> dict:
        """Конвертация в словарь для JSON"""
        return {
            'account_type': self.get_account_type(),
            'account_number': self._account_number,
            'owner_name': self._owner_name,
            'balance': self._balance,
            'is_active': self._is_active,
            'transaction_history': [t.to_dict() for t in self._transaction_history.get_all_transactions()]
        }
    
    def __str__(self):
        status = "Активен" if self._is_active else "Заблокирован"
        return f"{self.get_account_type()} | {self._account_number} | {self._owner_name} | {self._balance:.2f}₽ | {status}"


class CheckingAccount(Account):
    """Расчетный счет"""
    
    def __init__(self, account_number: str, owner_name: str, balance: float = 0.0, overdraft_limit: float = 0.0):
        super().__init__(account_number, owner_name, balance)
        self.overdraft_limit = overdraft_limit
    
    def withdraw(self, amount: float, description: str = "") -> bool:
        """Снятие с возможным овердрафтом"""
        if not self._is_active:
            raise ValueError("Счет заблокирован")
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        if amount > self._balance + self.overdraft_limit:
            raise ValueError(f"Превышен лимит овердрафта. Доступно: {self._balance + self.overdraft_limit:.2f}₽")
        
        self._balance -= amount
        transaction = Transaction(
            TransactionType.WITHDRAW, amount,
            description=f"Снятие: {description}" if description else "Снятие средств"
        )
        self._transaction_history.add_transaction(transaction)
        return True
    
    def get_account_type(self) -> str:
        return "Расчетный счет"
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data['overdraft_limit'] = self.overdraft_limit
        return data


class SavingsAccount(Account):
    """Сберегательный счет с процентами"""
    
    def __init__(self, account_number: str, owner_name: str, balance: float = 0.0, interest_rate: float = 5.0):
        super().__init__(account_number, owner_name, balance)
        self.interest_rate = interest_rate
    
    def apply_interest(self) -> None:
        """Начисление процентов"""
        interest = self._balance * (self.interest_rate / 100)
        self._balance += interest
        transaction = Transaction(
            TransactionType.INTEREST, interest,
            description=f"Начисление процентов по ставке {self.interest_rate}%"
        )
        self._transaction_history.add_transaction(transaction)
    
    def get_account_type(self) -> str:
        return "Сберегательный счет"
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data['interest_rate'] = self.interest_rate
        return data


class CreditAccount(Account):
    """Кредитный счет"""
    
    def __init__(self, account_number: str, owner_name: str, balance: float = 0.0, 
                 credit_limit: float = 100000, interest_rate: float = 20.0):
        super().__init__(account_number, owner_name, balance)
        self.credit_limit = credit_limit
        self.interest_rate = interest_rate
    
    @property
    def available_credit(self) -> float:
        """Доступный кредитный лимит"""
        return self.credit_limit + self._balance if self._balance < 0 else self.credit_limit
    
    def withdraw(self, amount: float, description: str = "") -> bool:
        """Снятие с использованием кредитного лимита"""
        if not self._is_active:
            raise ValueError("Счет заблокирован")
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        if amount > self._balance + self.credit_limit:
            raise ValueError(f"Превышен кредитный лимит. Доступно: {self._balance + self.credit_limit:.2f}₽")
        
        self._balance -= amount
        transaction = Transaction(
            TransactionType.WITHDRAW, amount,
            description=f"Снятие: {description}" if description else "Снятие средств"
        )
        self._transaction_history.add_transaction(transaction)
        
        # Если ушли в минус, начисляем комиссию
        if self._balance < 0:
            fee = abs(self._balance) * 0.01  # 1% комиссия за использование кредита
            self._balance -= fee
            fee_transaction = Transaction(
                TransactionType.FEE, fee,
                description=f"Комиссия за использование кредитных средств"
            )
            self._transaction_history.add_transaction(fee_transaction)
        
        return True
    
    def get_account_type(self) -> str:
        return "Кредитный счет"
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data['credit_limit'] = self.credit_limit
        data['interest_rate'] = self.interest_rate
        return data


# ==================== МОДЕЛЬ (Model) ====================

class BankModel:
    """Model: Управление данными и бизнес-логикой"""
    
    def __init__(self):
        self.accounts: Dict[str, Account] = {}
        self.data_file = "bank_data.json"
        self.load_data()
    
    def create_account(self, account_type: str, account_number: str, owner_name: str, 
                      initial_balance: float = 0.0, **kwargs) -> Account:
        """Создание нового счета"""
        if account_number in self.accounts:
            raise ValueError(f"Счет с номером {account_number} уже существует")
        
        if account_type == "checking":
            account = CheckingAccount(account_number, owner_name, initial_balance, 
                                     kwargs.get('overdraft_limit', 0.0))
        elif account_type == "savings":
            account = SavingsAccount(account_number, owner_name, initial_balance,
                                    kwargs.get('interest_rate', 5.0))
        elif account_type == "credit":
            account = CreditAccount(account_number, owner_name, initial_balance,
                                   kwargs.get('credit_limit', 100000),
                                   kwargs.get('interest_rate', 20.0))
        else:
            raise ValueError(f"Неизвестный тип счета: {account_type}")
        
        self.accounts[account_number] = account
        self.save_data()
        return account
    
    def get_account(self, account_number: str) -> Optional[Account]:
        """Получение счета по номеру"""
        return self.accounts.get(account_number)
    
    def get_all_accounts(self) -> List[Account]:
        """Получение всех счетов"""
        return list(self.accounts.values())
    
    def delete_account(self, account_number: str) -> bool:
        """Удаление счета"""
        if account_number in self.accounts:
            del self.accounts[account_number]
            self.save_data()
            return True
        return False
    
    def transfer_between_accounts(self, from_account: str, to_account: str, amount: float, 
                                  description: str = "") -> bool:
        """Перевод между счетами"""
        from_acc = self.get_account(from_account)
        to_acc = self.get_account(to_account)
        
        if not from_acc or not to_acc:
            raise ValueError("Один из счетов не найден")
        
        result = from_acc.transfer_to(to_acc, amount, description)
        if result:
            self.save_data()
        return result
    
    def apply_interest_to_all_savings(self) -> None:
        """Начисление процентов на все сберегательные счета"""
        for account in self.accounts.values():
            if isinstance(account, SavingsAccount):
                account.apply_interest()
        self.save_data()
    
    def save_data(self) -> None:
        """Сохранение данных в JSON"""
        data = {
            'accounts': [acc.to_dict() for acc in self.accounts.values()]
        }
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    def load_data(self) -> None:
        """Загрузка данных из JSON"""
        if not os.path.exists(self.data_file):
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.accounts.clear()
            for acc_data in data.get('accounts', []):
                account_type = acc_data['account_type']
                account_number = acc_data['account_number']
                owner_name = acc_data['owner_name']
                balance = acc_data['balance']
                is_active = acc_data['is_active']
                
                if account_type == "Расчетный счет":
                    account = CheckingAccount(account_number, owner_name, balance, 
                                             acc_data.get('overdraft_limit', 0.0))
                elif account_type == "Сберегательный счет":
                    account = SavingsAccount(account_number, owner_name, balance,
                                            acc_data.get('interest_rate', 5.0))
                elif account_type == "Кредитный счет":
                    account = CreditAccount(account_number, owner_name, balance,
                                           acc_data.get('credit_limit', 100000),
                                           acc_data.get('interest_rate', 20.0))
                else:
                    continue
                
                account._is_active = is_active
                # Загрузка истории транзакций
                for trans_data in acc_data.get('transaction_history', []):
                    transaction = Transaction.from_dict(trans_data)
                    account._transaction_history.add_transaction(transaction)
                
                self.accounts[account_number] = account
                
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ Ошибка загрузки данных: {e}")


# ==================== ПРЕДСТАВЛЕНИЕ (View) ====================

class BankView:
    """View: Отображение информации и взаимодействие с пользователем"""
    
    @staticmethod
    def display_menu():
        """Отображение главного меню"""
        print("\n" + "="*60)
        print("🏦 БАНКОВСКАЯ СИСТЕМА")
        print("="*60)
        print("1. 📋 Просмотр всех счетов")
        print("2. ➕ Создать новый счет")
        print("3. 💰 Пополнить счет")
        print("4. 💸 Снять средства")
        print("5. 🔄 Перевести средства")
        print("6. 📜 История транзакций")
        print("7. 🔍 Фильтрация транзакций")
        print("8. 📈 Начислить проценты (сберегательные счета)")
        print("9. 🔒 Заблокировать/разблокировать счет")
        print("10. 🗑️ Удалить счет")
        print("0. 🚪 Выход")
        print("="*60)
    
    @staticmethod
    def display_accounts(accounts: List[Account]):
        """Отображение списка счетов"""
        if not accounts:
            print("\n📭 Нет открытых счетов")
            return
        
        print("\n" + "="*80)
        print("СПИСОК СЧЕТОВ")
        print("="*80)
        for account in accounts:
            print(account)
        print("="*80)
    
    @staticmethod
    def display_transactions(transactions: List[Transaction], title: str = "ИСТОРИЯ ТРАНЗАКЦИЙ"):
        """Отображение транзакций"""
        if not transactions:
            print("\n📭 Нет транзакций для отображения")
            return
        
        print(f"\n{'='*80}")
        print(f"{title}")
        print(f"{'='*80}")
        for transaction in transactions:
            print(transaction)
        print(f"{'='*80}")
    
    @staticmethod
    def get_input(prompt: str, input_type: type = str, allow_negative: bool = False) -> Any:
        """Получение ввода с валидацией"""
        while True:
            try:
                value = input(prompt)
                if input_type == float:
                    value = float(value)
                    if not allow_negative and value < 0:
                        print("❌ Значение не может быть отрицательным")
                        continue
                elif input_type == int:
                    value = int(value)
                    if not allow_negative and value < 0:
                        print("❌ Значение не может быть отрицательным")
                        continue
                return value
            except ValueError:
                print(f"❌ Ошибка: Введите корректное значение ({input_type.__name__})")
    
    @staticmethod
    def get_date_input(prompt: str) -> Optional[datetime]:
        """Получение даты с валидацией"""
        while True:
            try:
                date_str = input(prompt)
                if not date_str:
                    return None
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                print("❌ Неверный формат даты. Используйте ГГГГ-ММ-ДД")
    
    @staticmethod
    def show_message(message: str, is_error: bool = False):
        """Отображение сообщения"""
        prefix = "❌" if is_error else "✅"
        print(f"{prefix} {message}")
    
    @staticmethod
    def get_account_type() -> str:
        """Выбор типа счета"""
        print("\nТипы счетов:")
        print("1. Расчетный счет (с возможностью овердрафта)")
        print("2. Сберегательный счет (с начислением процентов)")
        print("3. Кредитный счет (с кредитным лимитом)")
        
        while True:
            choice = input("Выберите тип счета (1-3): ")
            if choice == '1':
                return "checking"
            elif choice == '2':
                return "savings"
            elif choice == '3':
                return "credit"
            else:
                print("❌ Неверный выбор. Попробуйте снова.")


# ==================== КОНТРОЛЛЕР (Controller) ====================

class BankController:
    """Controller: Управление бизнес-логикой и обработка запросов"""
    
    def __init__(self, model: BankModel, view: BankView):
        self.model = model
        self.view = view
    
    def run(self):
        """Запуск приложения"""
        self.view.show_message("Добро пожаловать в банковскую систему!")
        
        while True:
            self.view.display_menu()
            choice = self.view.get_input("Выберите действие (0-10): ", int)
            
            if choice == 0:
                self.view.show_message("До свидания!")
                break
            elif choice == 1:
                self.show_all_accounts()
            elif choice == 2:
                self.create_account()
            elif choice == 3:
                self.deposit_money()
            elif choice == 4:
                self.withdraw_money()
            elif choice == 5:
                self.transfer_money()
            elif choice == 6:
                self.show_transaction_history()
            elif choice == 7:
                self.filter_transactions()
            elif choice == 8:
                self.apply_interest()
            elif choice == 9:
                self.toggle_account_status()
            elif choice == 10:
                self.delete_account()
            else:
                self.view.show_message("Неверный выбор", True)
    
    def show_all_accounts(self):
        """Показать все счета"""
        accounts = self.model.get_all_accounts()
        self.view.display_accounts(accounts)
    
    def create_account(self):
        """Создание нового счета"""
        try:
            print("\n--- Создание нового счета ---")
            account_type = self.view.get_account_type()
            account_number = self.view.get_input("Введите номер счета: ", str)
            owner_name = self.view.get_input("Введите ФИО владельца: ", str)
            initial_balance = self.view.get_input("Начальный баланс (₽): ", float)
            
            kwargs = {}
            if account_type == "checking":
                overdraft = self.view.get_input("Лимит овердрафта (₽): ", float)
                kwargs['overdraft_limit'] = overdraft
            elif account_type == "savings":
                rate = self.view.get_input("Процентная ставка (%): ", float)
                kwargs['interest_rate'] = rate
            elif account_type == "credit":
                limit = self.view.get_input("Кредитный лимит (₽): ", float)
                rate = self.view.get_input("Процентная ставка (%): ", float)
                kwargs['credit_limit'] = limit
                kwargs['interest_rate'] = rate
            
            account = self.model.create_account(account_type, account_number, owner_name, initial_balance, **kwargs)
            self.view.show_message(f"Счет успешно создан!\n{account}")
            
        except ValueError as e:
            self.view.show_message(str(e), True)
    
    def deposit_money(self):
        """Пополнение счета"""
        try:
            print("\n--- Пополнение счета ---")
            account_number = self.view.get_input("Номер счета: ", str)
            account = self.model.get_account(account_number)
            
            if not account:
                self.view.show_message("Счет не найден", True)
                return
            
            amount = self.view.get_input("Сумма пополнения (₽): ", float)
            description = self.view.get_input("Описание (необязательно): ", str) or ""
            
            account.deposit(amount, description)
            self.model.save_data()
            self.view.show_message(f"Счет пополнен на {amount:.2f}₽. Новый баланс: {account.balance:.2f}₽")
            
        except ValueError as e:
            self.view.show_message(str(e), True)
    
    def withdraw_money(self):
        """Снятие средств"""
        try:
            print("\n--- Снятие средств ---")
            account_number = self.view.get_input("Номер счета: ", str)
            account = self.model.get_account(account_number)
            
            if not account:
                self.view.show_message("Счет не найден", True)
                return
            
            amount = self.view.get_input("Сумма снятия (₽): ", float)
            description = self.view.get_input("Описание (необязательно): ", str) or ""
            
            account.withdraw(amount, description)
            self.model.save_data()
            self.view.show_message(f"Снято {amount:.2f}₽. Новый баланс: {account.balance:.2f}₽")
            
        except ValueError as e:
            self.view.show_message(str(e), True)
    
    def transfer_money(self):
        """Перевод средств"""
        try:
            print("\n--- Перевод средств ---")
            from_account = self.view.get_input("Счет списания: ", str)
            to_account = self.view.get_input("Счет зачисления: ", str)
            amount = self.view.get_input("Сумма перевода (₽): ", float)
            description = self.view.get_input("Описание (необязательно): ", str) or ""
            
            self.model.transfer_between_accounts(from_account, to_account, amount, description)
            self.view.show_message(f"Переведено {amount:.2f}₽ со счета {from_account} на счет {to_account}")
            
        except ValueError as e:
            self.view.show_message(str(e), True)
    
    def show_transaction_history(self):
        """Показать историю транзакций"""
        account_number = self.view.get_input("Номер счета: ", str)
        account = self.model.get_account(account_number)
        
        if not account:
            self.view.show_message("Счет не найден", True)
            return
        
        transactions = account.get_transaction_history()
        self.view.display_transactions(transactions, f"ИСТОРИЯ ТРАНЗАКЦИЙ (счет {account_number})")
    
    def filter_transactions(self):
        """Фильтрация транзакций"""
        account_number = self.view.get_input("Номер счета: ", str)
        account = self.model.get_account(account_number)
        
        if not account:
            self.view.show_message("Счет не найден", True)
            return
        
        print("\n--- Фильтрация транзакций ---")
        print("1. По типу транзакции")
        print("2. По диапазону дат")
        print("3. По типу и дате")
        
        choice = self.view.get_input("Выберите тип фильтрации (1-3): ", int)
        
        transactions = []
        
        if choice == 1:
            print("\nТипы транзакций:")
            for i, ttype in enumerate(TransactionType, 1):
                print(f"{i}. {ttype.value}")
            type_choice = self.view.get_input("Выберите тип (1-4): ", int)
            if 1 <= type_choice <= len(TransactionType):
                ttype = list(TransactionType)[type_choice - 1]
                transactions = account.filter_transactions_by_type(ttype)
                self.view.display_transactions(transactions, f"Транзакции типа: {ttype.value}")
        
        elif choice == 2:
            start_date = self.view.get_date_input("Начальная дата (ГГГГ-ММ-ДД) или Enter для пропуска: ")
            end_date = self.view.get_date_input("Конечная дата (ГГГГ-ММ-ДД) или Enter для пропуска: ")
            
            if start_date and end_date:
                transactions = account.filter_transactions_by_date(start_date, end_date)
                self.view.display_transactions(transactions, f"Транзакции за период: {start_date.date()} - {end_date.date()}")
            else:
                self.view.show_message("Необходимо указать обе даты", True)
        
        elif choice == 3:
            print("\nТипы транзакций:")
            for i, ttype in enumerate(TransactionType, 1):
                print(f"{i}. {ttype.value}")
            type_choice = self.view.get_input("Выберите тип (1-4): ", int)
            
            if 1 <= type_choice <= len(TransactionType):
                ttype = list(TransactionType)[type_choice - 1]
                filtered_by_type = account.filter_transactions_by_type(ttype)
                
                start_date = self.view.get_date_input("Начальная дата (ГГГГ-ММ-ДД): ")
                end_date = self.view.get_date_input("Конечная дата (ГГГГ-ММ-ДД): ")
                
                if start_date and end_date:
                    transactions = [t for t in filtered_by_type if start_date <= t.date <= end_date]
                    self.view.display_transactions(transactions, f"Транзакции: {ttype.value} за период")
        else:
            self.view.show_message("Неверный выбор", True)
    
    def apply_interest(self):
        """Начисление процентов на сберегательные счета"""
        try:
            self.model.apply_interest_to_all_savings()
            self.view.show_message("Проценты начислены на все сберегательные счета")
        except Exception as e:
            self.view.show_message(str(e), True)
    
    def toggle_account_status(self):
        """Блокировка/разблокировка счета"""
        account_number = self.view.get_input("Номер счета: ", str)
        account = self.model.get_account(account_number)
        
        if not account:
            self.view.show_message("Счет не найден", True)
            return
        
        if account.is_active:
            account.deactivate()
            self.view.show_message(f"Счет {account_number} заблокирован")
        else:
            account.activate()
            self.view.show_message(f"Счет {account_number} разблокирован")
        
        self.model.save_data()
    
    def delete_account(self):
        """Удаление счета"""
        account_number = self.view.get_input("Номер счета для удаления: ", str)
        account = self.model.get_account(account_number)
        
        if not account:
            self.view.show_message("Счет не найден", True)
            return
        
        confirm = input(f"Вы уверены, что хотите удалить счет {account_number}? (y/n): ").lower()
        if confirm == 'y':
            self.model.delete_account(account_number)
            self.view.show_message(f"Счет {account_number} удален")
        else:
            self.view.show_message("Операция отменена")


# ==================== ЗАПУСК ПРИЛОЖЕНИЯ ====================

def main():
    """Главная функция запуска приложения"""
    model = BankModel()
    view = BankView()
    controller = BankController(model, view)
    controller.run()


if __name__ == "__main__":
    main()
