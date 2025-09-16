#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализатор торговых сделок
Читает файлы сделок и вычисляет средние значения
"""

import pandas as pd
import os
import shutil
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trades_analyzer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TradesAnalyzer:
    """Класс для анализа торговых сделок"""
    
    def __init__(self, trades_directory: str = None):
        """
        Инициализация анализатора
        
        Args:
            trades_directory: Путь к директории с файлами сделок (если None, то будет выбор)
        """
        # Если директория не указана, предлагаем выбор
        if trades_directory is None:
            trades_directory = self._choose_source_directory()
        
        self.trades_directory = trades_directory
        self.input_directory = os.path.join(os.getcwd(), "input")
        
        # Создаем папку input если её нет
        if not os.path.exists(self.input_directory):
            os.makedirs(self.input_directory)
            logger.info(f"Создана папка для входных файлов: {self.input_directory}")
    
    def _choose_source_directory(self) -> str:
        """
        Позволяет пользователю выбрать источник файлов
        
        Returns:
            Путь к выбранной директории
        """
        # Определяем путь к рабочему столу через стандартные переменные Windows
        userprofile = os.environ.get('USERPROFILE', os.path.expanduser("~"))
        
        # Пробуем разные варианты рабочего стола
        desktop_variants = [
            os.path.join(userprofile, "Desktop"),
            os.path.join(userprofile, "OneDrive", "Desktop"), 
            os.path.join(userprofile, "OneDrive", "Рабочий стол"),
            os.path.join(userprofile, "Рабочий стол")
        ]
        
        desktop_path = None
        for variant in desktop_variants:
            if os.path.exists(variant):
                desktop_path = variant
                break
        
        # Если не нашли, используем USERPROFILE
        if desktop_path is None:
            desktop_path = userprofile
        
        # Используем найденные рабочие пути
        kas_path = r"C:\Sandbox\glaze\Kas\user\current\OneDrive\Рабочий стол"
        # Используем точный путь к рабочему столу через USERPROFILE
        desktop_real_path = os.path.join(os.environ.get('USERPROFILE', ''), "OneDrive", "Рабочий стол")
        
        sources = {
            1: {
                "name": "Папка Kas (основной источник)",
                "path": kas_path
            },
            2: {
                "name": "Рабочий стол пользователя", 
                "path": desktop_real_path
            }
        }
        
        print("\n" + "="*60)
        print("📁 ВЫБОР ИСТОЧНИКА ФАЙЛОВ СДЕЛОК")
        print("="*60)
        
        for key, source in sources.items():
            status = "✅" if os.path.exists(source["path"]) else "❌"
            print(f"{key}. {source['name']}")
            print(f"   Путь: {source['path']}")
            print(f"   Статус: {status} {'Доступна' if os.path.exists(source['path']) else 'Недоступна'}")
            print()
        
        while True:
            try:
                choice = input("Выберите источник (1 или 2): ").strip()
                choice_num = int(choice)
                
                if choice_num in sources:
                    selected_source = sources[choice_num]
                    if os.path.exists(selected_source["path"]):
                        print(f"✅ Выбран источник: {selected_source['name']}")
                        print(f"📁 Путь: {selected_source['path']}")
                        return selected_source["path"]
                    else:
                        print(f"❌ Папка недоступна: {selected_source['path']}")
                        print("Попробуйте другой вариант.")
                else:
                    print("❌ Неверный выбор. Введите 1 или 2.")
                    
            except ValueError:
                print("❌ Введите число 1 или 2.")
            except KeyboardInterrupt:
                print("\n❌ Отменено пользователем.")
                sys.exit(1)
        
    def get_today_trades_file(self) -> Optional[str]:
        """
        Получает путь к файлу сделок за сегодня
        
        Returns:
            Путь к файлу или None если файл не найден
        """
        today = datetime.now().strftime("%d.%m.%Y")
        filename = f"Trades_{today}.csv"
        filepath = os.path.join(self.trades_directory, filename)
        
        if os.path.exists(filepath):
            logger.info(f"Найден файл сделок: {filepath}")
            return filepath
        else:
            logger.warning(f"Файл сделок не найден: {filepath}")
            return None
    
    def copy_file_to_input(self, source_filepath: str) -> str:
        """
        Копирует файл в папку input с добавлением метки источника
        
        Args:
            source_filepath: Путь к исходному файлу
            
        Returns:
            Путь к скопированному файлу
        """
        try:
            filename = os.path.basename(source_filepath)
            name, ext = os.path.splitext(filename)
            
            # Определяем метку источника
            source_tag = ""
            if "Sandbox" in source_filepath and "Kas" in source_filepath:
                source_tag = "_Ваня"
            elif "OneDrive" in source_filepath and "Рабочий стол" in source_filepath:
                source_tag = "_супруга_и_дочь"
            elif "Desktop" in source_filepath:
                source_tag = "_супруга_и_дочь"
            
            # Добавляем метку к имени файла
            if source_tag:
                filename = f"{name}{source_tag}{ext}"
            
            destination = os.path.join(self.input_directory, filename)
            
            # Если файл уже существует, добавляем timestamp
            if os.path.exists(destination):
                timestamp = datetime.now().strftime("%H%M%S")
                filename = f"{name}{source_tag}_{timestamp}{ext}"
                destination = os.path.join(self.input_directory, filename)
            
            shutil.copy2(source_filepath, destination)
            logger.info(f"Файл скопирован в input: {filename}")
            return destination
            
        except Exception as e:
            logger.error(f"Ошибка при копировании файла: {e}")
            return source_filepath  # Возвращаем оригинальный путь если копирование не удалось
    
    def create_and_open_excel(self, df: pd.DataFrame, source_filepath: str) -> str:
        """
        Создает Excel файл из DataFrame и открывает его
        
        Args:
            df: DataFrame с данными
            source_filepath: Путь к исходному файлу для формирования имени
            
        Returns:
            Путь к созданному Excel файлу
        """
        try:
            # Формируем имя Excel файла
            base_name = os.path.splitext(os.path.basename(source_filepath))[0]
            excel_filename = f"{base_name}_analyzed.xlsx"
            excel_path = os.path.join(self.input_directory, excel_filename)
            
            # Создаем Excel файл с несколькими листами
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                # Основные данные
                df.to_excel(writer, sheet_name='Данные', index=False)
                
                # Статистика по столбцам
                stats_data = []
                for col in df.columns:
                    if col in ['Price', 'Amount']:
                        numeric_col = pd.to_numeric(df[col], errors='coerce')
                        stats_data.append({
                            'Столбец': col,
                            'Тип': str(df[col].dtype),
                            'Всего значений': len(df[col]),
                            'Пустых': df[col].isna().sum(),
                            'Валидных числовых': numeric_col.notna().sum() if not numeric_col.empty else 0,
                            'Минимум': numeric_col.min() if numeric_col.notna().any() else 'N/A',
                            'Максимум': numeric_col.max() if numeric_col.notna().any() else 'N/A',
                            'Среднее': numeric_col.mean() if numeric_col.notna().any() else 'N/A',
                            'Сумма': numeric_col.sum() if numeric_col.notna().any() else 'N/A'
                        })
                    else:
                        stats_data.append({
                            'Столбец': col,
                            'Тип': str(df[col].dtype),
                            'Всего значений': len(df[col]),
                            'Пустых': df[col].isna().sum(),
                            'Уникальных': df[col].nunique(),
                            'Примеры': ', '.join(map(str, df[col].dropna().head(3).tolist()))
                        })
                
                stats_df = pd.DataFrame(stats_data)
                stats_df.to_excel(writer, sheet_name='Статистика', index=False)
                
                
                # Анализ по тикерам (если есть результаты анализа)
                if hasattr(self, '_last_ticker_analysis') and self._last_ticker_analysis:
                    ticker_summary = []
                    for ticker, data in self._last_ticker_analysis.items():
                        row = {
                            'Тикер': ticker,
                            'Всего сделок': data.get('total_trades', 0),
                            'Buy сделок': data.get('buy_trades', 0),
                            'Sell сделок': data.get('sell_trades', 0),
                            'Средняя цена': data.get('avg_price', 'N/A'),
                            'Мин цена': data.get('min_price', 'N/A'),
                            'Макс цена': data.get('max_price', 'N/A'),
                            'VWAP': data.get('vwap', 'N/A'),
                            'Средний объем': data.get('avg_amount', 'N/A'),
                            'Общий объем': data.get('total_amount', 'N/A'),
                            'Чистый объем (Buy-Sell)': data.get('net_amount', 'N/A'),
                            'Оборот': data.get('total_turnover', 'N/A')
                        }
                        ticker_summary.append(row)
                    
                    if ticker_summary:
                        ticker_df = pd.DataFrame(ticker_summary)
                        ticker_df.to_excel(writer, sheet_name='Анализ_по_тикерам', index=False)
                
                # Сделки текущей сессии (исключая переносы с 00:00:00)
                if hasattr(self, '_last_current_session_analysis') and self._last_current_session_analysis:
                    current_session_data = self._last_current_session_analysis
                    
                    # Лист с сделками текущей сессии
                    if 'current_session_dataframe' in current_session_data:
                        current_df = current_session_data['current_session_dataframe']
                        if len(current_df) > 0:
                            current_df.to_excel(writer, sheet_name='Текущая_сессия', index=False)
                    
                    # Анализ по тикерам для текущей сессии
                    if 'current_session_ticker_analysis' in current_session_data:
                        current_ticker_summary = []
                        for ticker, data in current_session_data['current_session_ticker_analysis'].items():
                            row = {
                                'Тикер': ticker,
                                'Сделок текущей сессии': data.get('current_session_trades', 0),
                                'Current Buy': data.get('current_buy_trades', 0),
                                'Current Sell': data.get('current_sell_trades', 0),
                                'Средняя цена сессии': data.get('current_avg_price', 'N/A'),
                                'Мин цена сессии': data.get('current_min_price', 'N/A'),
                                'Макс цена сессии': data.get('current_max_price', 'N/A'),
                                'VWAP текущей сессии': data.get('current_vwap', 'N/A'),
                                'Средний объем сессии': data.get('current_avg_amount', 'N/A'),
                                'Общий объем сессии': data.get('current_total_amount', 'N/A'),
                                'Чистый объем сессии (Buy-Sell)': data.get('current_net_amount', 'N/A'),
                                'Оборот сессии': data.get('current_turnover', 'N/A')
                            }
                            current_ticker_summary.append(row)
                        
                        if current_ticker_summary:
                            current_ticker_df = pd.DataFrame(current_ticker_summary)
                            current_ticker_df.to_excel(writer, sheet_name='Сессия_по_тикерам', index=False)
                
                # Настраиваем ширину столбцов для всех листов (в самом конце)
                self._adjust_column_widths(writer)
                
                # Устанавливаем активный лист "Сессия_по_тикерам" при открытии
                if 'Сессия_по_тикерам' in writer.sheets:
                    workbook = writer.book
                    workbook.active = writer.sheets['Сессия_по_тикерам']
                    logger.info("Установлен активный лист: Сессия_по_тикерам")
            
            logger.info(f"Excel файл создан: {excel_filename}")
            
            # Открываем Excel файл
            try:
                if sys.platform == "win32":
                    os.startfile(excel_path)
                elif sys.platform == "darwin":  # macOS
                    subprocess.run(["open", excel_path])
                else:  # Linux
                    subprocess.run(["xdg-open", excel_path])
                
                logger.info(f"Excel файл открыт: {excel_filename}")
                
                # Файл открыт автоматически для просмотра
                logger.info("Финальный аналитический Excel файл открыт для просмотра")
                
            except Exception as e:
                logger.warning(f"Не удалось автоматически открыть Excel файл: {e}")
                logger.info(f"Вы можете открыть файл вручную: {excel_path}")
                
            return excel_path
            
        except Exception as e:
            logger.error(f"Ошибка при создании Excel файла: {e}")
            return ""
    
    def _adjust_column_widths(self, writer):
        """
        Автоматически настраивает ширину столбцов для всех листов в Excel файле
        
        Args:
            writer: ExcelWriter объект
        """
        try:
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                
                # Автоматическая ширина столбцов
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    
                    # Проходим по всем ячейкам в столбце
                    for cell in column:
                        try:
                            cell_value = str(cell.value) if cell.value is not None else ""
                            # Учитываем длину содержимого ячейки
                            if len(cell_value) > max_length:
                                max_length = len(cell_value)
                        except:
                            pass
                    
                    # Устанавливаем ширину с запасом
                    # Минимум 10 символов, максимум 60, плюс запас 3 символа
                    adjusted_width = max(10, min(max_length + 3, 60))
                    
                    # Для некоторых типов столбцов устанавливаем минимальную ширину
                    if any(keyword in str(column[0].value).lower() for keyword in ['цена', 'price', 'vwap', 'оборот', 'объем']):
                        adjusted_width = max(adjusted_width, 15)
                    
                    worksheet.column_dimensions[column_letter].width = adjusted_width
                    
                logger.info(f"Настроена ширина столбцов для листа '{sheet_name}'")
                    
        except Exception as e:
            logger.warning(f"Ошибка при настройке ширины столбцов: {e}")
    
    def create_parsed_excel(self, df: pd.DataFrame, source_filepath: str) -> str:
        """
        Создает простой Excel файл с распарсенными данными
        
        Args:
            df: DataFrame с данными
            source_filepath: Путь к исходному файлу
            
        Returns:
            Путь к созданному Excel файлу
        """
        try:
            # Формируем имя Excel файла
            base_name = os.path.splitext(os.path.basename(source_filepath))[0]
            excel_filename = f"{base_name}_parsed.xlsx"
            excel_path = os.path.join(self.input_directory, excel_filename)
            
            # Создаем простой Excel файл только с данными
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Распарсенные_данные', index=False)
                
                # Настраиваем ширину столбцов
                self._adjust_column_widths(writer)
            
            logger.info(f"Распарсенный Excel файл создан: {excel_filename}")
            return excel_path
            
        except Exception as e:
            logger.error(f"Ошибка при создании распарсенного Excel файла: {e}")
            return ""
    
    def load_trades(self, filepath: str) -> Optional[pd.DataFrame]:
        """
        Загружает данные о сделках из CSV файла
        
        Args:
            filepath: Путь к CSV файлу
            
        Returns:
            DataFrame с данными о сделках или None при ошибке
        """
        try:
            # Пробуем разные кодировки и разделители
            encodings = ['utf-8', 'cp1251', 'windows-1251', 'utf-8-sig']
            separators = [';', ',', '\t', '|', '/']
            
            for encoding in encodings:
                for sep in separators:
                    try:
                        df = pd.read_csv(filepath, encoding=encoding, sep=sep)
                        
                        # Проверяем, что данные разделились правильно
                        if len(df.columns) > 1:
                            logger.info(f"Файл успешно загружен с кодировкой {encoding} и разделителем '{sep}'")
                            logger.info(f"Загружено {len(df)} строк, {len(df.columns)} столбцов")
                            logger.info(f"Столбцы: {list(df.columns)}")
                            return df
                        elif len(df.columns) == 1:
                            # Если один столбец, пробуем разделить его вручную
                            column_name = df.columns[0]
                            if '/' in column_name:
                                # Разделяем заголовок
                                headers = column_name.split('/')
                                # Разделяем данные
                                data_rows = []
                                for _, row in df.iterrows():
                                    row_data = str(row[column_name]).strip()
                                    # Пропускаем пустые строки
                                    if not row_data or row_data == 'nan':
                                        continue
                                    values = row_data.split('/')
                                    if len(values) == len(headers):
                                        # Очищаем пустые значения и заменяем запятые на точки в числах
                                        cleaned_values = []
                                        for i, val in enumerate(values):
                                            val = val.strip()
                                            # Для Price, Fee, Amount заменяем запятые на точки
                                            if headers[i] in ['Price', 'Fee', 'Amount'] and val:
                                                val = val.replace(',', '.')
                                            # Заменяем пустые строки на None для численных полей
                                            if val == '' and headers[i] in ['Price', 'Fee', 'Amount']:
                                                val = None
                                            cleaned_values.append(val)
                                        data_rows.append(cleaned_values)
                                
                                if data_rows:
                                    new_df = pd.DataFrame(data_rows, columns=headers)
                                    # Пытаемся преобразовать численные столбцы
                                    for col in new_df.columns:
                                        if col in ['Price', 'Fee', 'Amount']:
                                            new_df[col] = pd.to_numeric(new_df[col], errors='coerce')
                                    
                                    logger.info(f"Файл разделен вручную: {len(new_df)} строк, {len(new_df.columns)} столбцов")
                                    logger.info(f"Столбцы: {list(new_df.columns)}")
                                    return new_df
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        logger.debug(f"Попытка с кодировкой {encoding} и разделителем '{sep}': {e}")
                        continue
            
            logger.error(f"Не удалось загрузить файл ни с одной из комбинаций")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке файла {filepath}: {e}")
            return None
    
    def calculate_averages(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Вычисляет средние и средневзвешенные значения по сделкам
        
        Args:
            df: DataFrame с данными о сделках
            
        Returns:
            Словарь со средними значениями
        """
        results = {}
        
        try:
            # Краткая информация о данных
            logger.info(f"Загружено {len(df)} строк с {len(df.columns)} столбцами: {list(df.columns)}")
            
            # Определяем численные столбцы
            numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
            
            if len(numeric_columns) == 0:
                logger.warning("Не найдено численных столбцов для расчета средних")
                # Попробуем принудительно преобразовать Price и Amount
                if 'Price' in df.columns and 'Amount' in df.columns:
                    logger.info("Пытаемся принудительно преобразовать Price и Amount в числа")
                    df_copy = df.copy()
                    df_copy['Price'] = pd.to_numeric(df_copy['Price'], errors='coerce')
                    df_copy['Amount'] = pd.to_numeric(df_copy['Amount'], errors='coerce')
                    
                    # Обновляем список численных столбцов
                    numeric_columns = df_copy.select_dtypes(include=['int64', 'float64']).columns
                    df = df_copy
                    logger.info(f"После преобразования численных столбцов: {list(numeric_columns)}")
            
            # Вычисляем простые средние для всех численных столбцов
            for col in numeric_columns:
                if not df[col].isna().all():  # Проверяем, что столбец не пустой
                    mean_value = df[col].mean()
                    results[f'avg_{col}'] = mean_value
            
            # Вычисляем средневзвешенные значения (VWAP)
            if 'Price' in df.columns and 'Amount' in df.columns:
                # Убираем строки с NaN значениями
                clean_df = df[['Price', 'Amount']].dropna()
                
                if len(clean_df) > 0:
                    # VWAP = Σ(Price × Amount) / Σ(Amount)
                    total_volume = clean_df['Amount'].sum()
                    if total_volume > 0:
                        vwap = (clean_df['Price'] * clean_df['Amount']).sum() / total_volume
                        results['vwap_price'] = vwap
                        
                        # Средний размер сделки взвешенный по цене
                        total_price_weight = clean_df['Price'].sum()
                        if total_price_weight > 0:
                            weighted_avg_amount = (clean_df['Amount'] * clean_df['Price']).sum() / total_price_weight
                            results['weighted_avg_amount'] = weighted_avg_amount
                    
                    # Дополнительная статистика
                    results['total_volume'] = total_volume
                    results['total_turnover'] = (clean_df['Price'] * clean_df['Amount']).sum()
                    results['valid_trades_count'] = len(clean_df)
            
            # Общая статистика
            results['total_trades'] = len(df)
            results['analysis_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Анализ по тикерам
            if 'Ticker' in df.columns:
                ticker_analysis = self.analyze_by_ticker(df)
                results['ticker_analysis'] = ticker_analysis
                # Сохраняем для использования в Excel
                self._last_ticker_analysis = ticker_analysis
            
            # Анализ сделок текущей сессии (исключая переносы с 00:00:00)
            current_session_analysis = self.analyze_current_session_trades(df)
            results['current_session_analysis'] = current_session_analysis
            # Сохраняем для использования в Excel
            self._last_current_session_analysis = current_session_analysis
            
        except Exception as e:
            logger.error(f"Ошибка при вычислении средних: {e}")
        
        return results
    
    def analyze_by_ticker(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """
        Анализирует сделки по каждому тикеру отдельно
        
        Args:
            df: DataFrame с данными о сделках
            
        Returns:
            Словарь с анализом по каждому тикеру
        """
        ticker_results = {}
        
        try:
            # Группируем по тикерам
            for ticker in df['Ticker'].unique():
                ticker_df = df[df['Ticker'] == ticker].copy()
                ticker_data = {}
                
                # Основная статистика
                ticker_data['total_trades'] = len(ticker_df)
                ticker_data['ticker'] = ticker
                
                # Анализ направлений сделок
                if 'Direction' in ticker_df.columns:
                    buy_trades = len(ticker_df[ticker_df['Direction'] == 'Buy'])
                    sell_trades = len(ticker_df[ticker_df['Direction'] == 'Sell'])
                    ticker_data['buy_trades'] = buy_trades
                    ticker_data['sell_trades'] = sell_trades
                
                # Анализ цен
                if 'Price' in ticker_df.columns:
                    prices = ticker_df['Price'].dropna()
                    if len(prices) > 0:
                        ticker_data['avg_price'] = prices.mean()
                        ticker_data['min_price'] = prices.min()
                        ticker_data['max_price'] = prices.max()
                        ticker_data['price_std'] = prices.std()
                        ticker_data['valid_price_trades'] = len(prices)
                
                # Анализ объемов
                if 'Amount' in ticker_df.columns:
                    amounts = ticker_df['Amount'].dropna()
                    if len(amounts) > 0:
                        ticker_data['avg_amount'] = amounts.mean()
                        ticker_data['total_amount'] = amounts.sum()
                        ticker_data['min_amount'] = amounts.min()
                        ticker_data['max_amount'] = amounts.max()
                        
                        # Чистый объем с учетом направления (Buy: +, Sell: -)
                        if 'Direction' in ticker_df.columns:
                            net_amount = 0
                            for _, row in ticker_df.iterrows():
                                if pd.notna(row['Amount']):
                                    if row['Direction'] == 'Buy':
                                        net_amount += row['Amount']
                                    elif row['Direction'] == 'Sell':
                                        net_amount -= row['Amount']
                            ticker_data['net_amount'] = net_amount
                
                # VWAP для тикера
                if 'Price' in ticker_df.columns and 'Amount' in ticker_df.columns:
                    clean_ticker_df = ticker_df[['Price', 'Amount']].dropna()
                    if len(clean_ticker_df) > 0:
                        total_volume = clean_ticker_df['Amount'].sum()
                        if total_volume > 0:
                            vwap = (clean_ticker_df['Price'] * clean_ticker_df['Amount']).sum() / total_volume
                            ticker_data['vwap'] = vwap
                            ticker_data['total_turnover'] = (clean_ticker_df['Price'] * clean_ticker_df['Amount']).sum()
                
                ticker_results[ticker] = ticker_data
                
        except Exception as e:
            logger.error(f"Ошибка при анализе по тикерам: {e}")
        
        return ticker_results
    
    def analyze_current_session_trades(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Анализирует только сделки текущей сессии (исключая переносы с 00:00:00)
        
        Args:
            df: DataFrame с данными о сделках
            
        Returns:
            Результаты анализа сделок текущей сессии
        """
        results = {}
        
        try:
            # Разделяем на переносы и текущую сессию
            if 'DateCreate' in df.columns:
                current_session_df = df[df['DateCreate'] != '00:00:00'].copy()
                transfers_df = df[df['DateCreate'] == '00:00:00'].copy()
                
                if len(current_session_df) == 0:
                    logger.warning("Нет сделок текущей сессии для анализа")
                    return {"error": "Нет сделок текущей сессии"}
                
                # Общая статистика сделок текущей сессии
                results['current_session_trades'] = len(current_session_df)
                results['transfers_trades'] = len(transfers_df)
                
                # Анализ направлений для сделок текущей сессии
                if 'Direction' in current_session_df.columns:
                    buy_trades = len(current_session_df[current_session_df['Direction'] == 'Buy'])
                    sell_trades = len(current_session_df[current_session_df['Direction'] == 'Sell'])
                    results['current_session_buy_trades'] = buy_trades
                    results['current_session_sell_trades'] = sell_trades
                
                # Анализ цен и объемов для сделок текущей сессии
                if 'Price' in current_session_df.columns and 'Amount' in current_session_df.columns:
                    clean_current_df = current_session_df[['Price', 'Amount']].dropna()
                    
                    if len(clean_current_df) > 0:
                        # Простые средние
                        results['current_session_avg_price'] = clean_current_df['Price'].mean()
                        results['current_session_avg_amount'] = clean_current_df['Amount'].mean()
                        results['current_session_total_volume'] = clean_current_df['Amount'].sum()
                        
                        # VWAP для сделок текущей сессии
                        total_volume = clean_current_df['Amount'].sum()
                        if total_volume > 0:
                            vwap = (clean_current_df['Price'] * clean_current_df['Amount']).sum() / total_volume
                            results['current_session_vwap'] = vwap
                            results['current_session_turnover'] = (clean_current_df['Price'] * clean_current_df['Amount']).sum()
                
                # Анализ по тикерам для сделок текущей сессии
                if 'Ticker' in current_session_df.columns:
                    current_session_ticker_analysis = {}
                    
                    for ticker in current_session_df['Ticker'].unique():
                        ticker_current_df = current_session_df[current_session_df['Ticker'] == ticker].copy()
                        ticker_data = {}
                        
                        ticker_data['current_session_trades'] = len(ticker_current_df)
                        
                        if 'Direction' in ticker_current_df.columns:
                            ticker_data['current_buy_trades'] = len(ticker_current_df[ticker_current_df['Direction'] == 'Buy'])
                            ticker_data['current_sell_trades'] = len(ticker_current_df[ticker_current_df['Direction'] == 'Sell'])
                        
                        if 'Price' in ticker_current_df.columns:
                            prices = ticker_current_df['Price'].dropna()
                            if len(prices) > 0:
                                ticker_data['current_avg_price'] = prices.mean()
                                ticker_data['current_min_price'] = prices.min()
                                ticker_data['current_max_price'] = prices.max()
                        
                        if 'Amount' in ticker_current_df.columns:
                            amounts = ticker_current_df['Amount'].dropna()
                            if len(amounts) > 0:
                                ticker_data['current_avg_amount'] = amounts.mean()
                                ticker_data['current_total_amount'] = amounts.sum()
                                
                                # Чистый объем текущей сессии с учетом направления (Buy: +, Sell: -)
                                if 'Direction' in ticker_current_df.columns:
                                    net_amount = 0
                                    for _, row in ticker_current_df.iterrows():
                                        if pd.notna(row['Amount']):
                                            if row['Direction'] == 'Buy':
                                                net_amount += row['Amount']
                                            elif row['Direction'] == 'Sell':
                                                net_amount -= row['Amount']
                                    ticker_data['current_net_amount'] = net_amount
                        
                        # VWAP для тикера (только текущая сессия)
                        if 'Price' in ticker_current_df.columns and 'Amount' in ticker_current_df.columns:
                            clean_ticker_df = ticker_current_df[['Price', 'Amount']].dropna()
                            if len(clean_ticker_df) > 0:
                                total_volume = clean_ticker_df['Amount'].sum()
                                if total_volume > 0:
                                    vwap = (clean_ticker_df['Price'] * clean_ticker_df['Amount']).sum() / total_volume
                                    ticker_data['current_vwap'] = vwap
                                    ticker_data['current_turnover'] = (clean_ticker_df['Price'] * clean_ticker_df['Amount']).sum()
                        
                        current_session_ticker_analysis[ticker] = ticker_data
                    
                    results['current_session_ticker_analysis'] = current_session_ticker_analysis
                
                # Сохраняем отфильтрованные данные для Excel
                results['current_session_dataframe'] = current_session_df
                
        except Exception as e:
            logger.error(f"Ошибка при анализе сделок текущей сессии: {e}")
        
        return results
    
    def analyze_today(self) -> Dict[str, Any]:
        """
        Анализирует сделки за сегодня
        
        Returns:
            Результаты анализа
        """
        logger.info("Начинаем анализ сделок за сегодня")
        
        # Получаем путь к файлу
        original_filepath = self.get_today_trades_file()
        if not original_filepath:
            return {"error": "Файл сделок за сегодня не найден"}
        
        # Копируем файл в папку input
        copied_filepath = self.copy_file_to_input(original_filepath)
        
        # Загружаем и парсим данные с разделителем "/"
        logger.info("Парсим CSV файл с разделителем '/'...")
        df = self.load_trades(copied_filepath)
        if df is None:
            return {"error": "Не удалось загрузить данные из файла"}
        
        # Создаем Excel файл с распарсенными данными (но не открываем)
        parsed_excel_path = self.create_parsed_excel(df, copied_filepath)
        
        # Вычисляем средние (включая анализ по тикерам)
        results = self.calculate_averages(df)
        
        # Создаем полный аналитический Excel файл (уже с данными по тикерам)
        excel_path = self.create_and_open_excel(df, copied_filepath)
        results['source_file'] = original_filepath
        results['copied_file'] = copied_filepath
        results['parsed_excel_file'] = parsed_excel_path
        results['excel_file'] = excel_path
        
        return results
    
    def print_results(self, results: Dict[str, Any]):
        """
        Выводит результаты анализа в консоль
        
        Args:
            results: Результаты анализа
        """
        if 'error' in results:
            print(f"❌ Ошибка: {results['error']}")
            return
        
        print("\n" + "="*60)
        print("📊 АНАЛИЗ ТОРГОВЫХ СДЕЛОК")
        print("="*60)
        
        if 'source_file' in results:
            print(f"📁 Исходный файл: {os.path.basename(results['source_file'])}")
        
        if 'copied_file' in results:
            print(f"📂 Скопирован в: {os.path.relpath(results['copied_file'])}")
        
        if 'parsed_excel_file' in results and results['parsed_excel_file']:
            print(f"📋 Распарсенный Excel: {os.path.relpath(results['parsed_excel_file'])}")
        
        if 'excel_file' in results and results['excel_file']:
            print(f"📊 Аналитический Excel: {os.path.relpath(results['excel_file'])}")
        
        if 'total_trades' in results:
            print(f"📈 Всего сделок: {results['total_trades']}")
        
        if 'valid_trades_count' in results:
            print(f"✅ Валидных сделок: {results['valid_trades_count']}")
        
        # Общая статистика
        if 'total_volume' in results:
            print(f"📦 Общий объем: {results['total_volume']:.4f}")
        
        if 'total_turnover' in results:
            print(f"💰 Общий оборот: {results['total_turnover']:,.2f} ₽")
        
        # Простые средние значения
        print("\n📊 ПРОСТЫЕ СРЕДНИЕ ЗНАЧЕНИЯ:")
        print("-" * 40)
        
        for key, value in results.items():
            if key.startswith('avg_'):
                column_name = key[4:]  # Убираем префикс 'avg_'
                if column_name == 'Price':
                    print(f"Средняя цена: {value:,.4f} ₽")
                elif column_name == 'Amount':
                    print(f"Средний объем: {value:.4f}")
                else:
                    print(f"{column_name}: {value:.4f}")
        
        # Средневзвешенные значения
        has_weighted = any(key in results for key in ['vwap_price', 'weighted_avg_amount'])
        if has_weighted:
            print("\n⚖️  СРЕДНЕВЗВЕШЕННЫЕ ЗНАЧЕНИЯ:")
            print("-" * 40)
            
            if 'vwap_price' in results:
                print(f"VWAP (средневзвешенная цена): {results['vwap_price']:,.4f} ₽")
            
            if 'weighted_avg_amount' in results:
                print(f"Средневзвешенный объем: {results['weighted_avg_amount']:.4f}")
        
        # Анализ по тикерам
        if 'ticker_analysis' in results and results['ticker_analysis']:
            print("\n📊 АНАЛИЗ ПО ТИКЕРАМ:")
            print("="*60)
            
            for ticker, data in results['ticker_analysis'].items():
                print(f"\n🔸 {ticker}:")
                print(f"   Сделок: {data.get('total_trades', 0)} (Buy: {data.get('buy_trades', 0)}, Sell: {data.get('sell_trades', 0)})")
                
                if 'avg_price' in data:
                    print(f"   Средняя цена: {data['avg_price']:,.4f} ₽")
                if 'min_price' in data and 'max_price' in data:
                    print(f"   Диапазон цен: {data['min_price']:,.4f} - {data['max_price']:,.4f} ₽")
                if 'vwap' in data:
                    print(f"   VWAP: {data['vwap']:,.4f} ₽")
                if 'avg_amount' in data:
                    print(f"   Средний объем: {data['avg_amount']:.2f}")
                if 'total_amount' in data:
                    print(f"   Общий объем: {data['total_amount']:.0f}")
                if 'net_amount' in data:
                    net_val = data['net_amount']
                    direction = "📈" if net_val > 0 else "📉" if net_val < 0 else "➡️"
                    print(f"   Чистый объем: {direction} {net_val:+.0f}")
                if 'total_turnover' in data:
                    print(f"   Оборот: {data['total_turnover']:,.2f} ₽")
        
        if 'analysis_date' in results:
            print(f"\n⏰ Дата анализа: {results['analysis_date']}")
        
        print("="*60)


def main():
    """Основная функция"""
    analyzer = TradesAnalyzer()
    results = analyzer.analyze_today()
    analyzer.print_results(results)


if __name__ == "__main__":
    main()
