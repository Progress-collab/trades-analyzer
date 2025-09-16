#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализатор торговых сделок
Читает файлы сделок и вычисляет средние значения
"""

import pandas as pd
import os
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
    
    def __init__(self, trades_directory: str = r"C:\Sandbox\glaze\Kas\user\current\OneDrive\Рабочий стол"):
        """
        Инициализация анализатора
        
        Args:
            trades_directory: Путь к директории с файлами сделок
        """
        self.trades_directory = trades_directory
        
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
                                    values = str(row[column_name]).split('/')
                                    if len(values) == len(headers):
                                        data_rows.append(values)
                                
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
            # Определяем численные столбцы
            numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
            
            if len(numeric_columns) == 0:
                logger.warning("Не найдено численных столбцов для расчета средних")
                return results
            
            # Вычисляем простые средние для всех численных столбцов
            for col in numeric_columns:
                if not df[col].isna().all():  # Проверяем, что столбец не пустой
                    mean_value = df[col].mean()
                    results[f'avg_{col}'] = mean_value
                    logger.info(f"Простое среднее {col}: {mean_value:.4f}")
            
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
                        logger.info(f"VWAP (средневзвешенная цена): {vwap:.4f}")
                        
                        # Средний размер сделки взвешенный по цене
                        total_price_weight = clean_df['Price'].sum()
                        if total_price_weight > 0:
                            weighted_avg_amount = (clean_df['Amount'] * clean_df['Price']).sum() / total_price_weight
                            results['weighted_avg_amount'] = weighted_avg_amount
                            logger.info(f"Средневзвешенный объем: {weighted_avg_amount:.4f}")
                    
                    # Дополнительная статистика
                    results['total_volume'] = total_volume
                    results['total_turnover'] = (clean_df['Price'] * clean_df['Amount']).sum()
                    
                    logger.info(f"Общий объем: {total_volume:.4f}")
                    logger.info(f"Общий оборот: {results['total_turnover']:.2f}")
            
            # Общая статистика
            results['total_trades'] = len(df)
            results['analysis_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            logger.info(f"Всего сделок: {results['total_trades']}")
            
        except Exception as e:
            logger.error(f"Ошибка при вычислении средних: {e}")
        
        return results
    
    def analyze_today(self) -> Dict[str, Any]:
        """
        Анализирует сделки за сегодня
        
        Returns:
            Результаты анализа
        """
        logger.info("Начинаем анализ сделок за сегодня")
        
        # Получаем путь к файлу
        filepath = self.get_today_trades_file()
        if not filepath:
            return {"error": "Файл сделок за сегодня не найден"}
        
        # Загружаем данные
        df = self.load_trades(filepath)
        if df is None:
            return {"error": "Не удалось загрузить данные из файла"}
        
        # Вычисляем средние
        results = self.calculate_averages(df)
        results['source_file'] = filepath
        
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
            print(f"📁 Файл: {os.path.basename(results['source_file'])}")
        
        if 'total_trades' in results:
            print(f"📈 Всего сделок: {results['total_trades']}")
        
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
