"""
Carregamento de dados históricos para reconciliação.

Este módulo carrega dados históricos de um mês/ano específico para recálculo
de comissões com dados corretos (reconciliação retroativa).
"""

import pandas as pd
import os
import sys
from typing import Dict, Tuple
from datetime import datetime

# Adicionar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import preparar_dados_mensais


class HistoricalDataLoader:
    """
    Carrega dados históricos para um mês/ano específico.
    
    Carrega:
    - Faturados do mês
    - Conversões do mês
    - Faturados YTD (year-to-date)
    - Retenção de clientes
    - Rentabilidade histórica (da pasta rentabilidades/)
    
    Attributes:
        base_path: Caminho base do projeto
        rentabilidades_path: Caminho da pasta de rentabilidades
    """
    
    def __init__(self, base_path: str = None):
        """
        Inicializa o loader.
        
        Args:
            base_path: Caminho base do projeto (usa cwd se None)
        """
        self.base_path = base_path or os.getcwd()
        self.rentabilidades_path = os.path.join(self.base_path, 'rentabilidades')
    
    def load_for_month(self, mes: int, ano: int) -> Dict[str, pd.DataFrame]:
        """
        Carrega todos os dados históricos para um mês/ano.
        
        Args:
            mes: Mês (1-12)
            ano: Ano (ex: 2025)
        
        Returns:
            Dicionário com DataFrames:
            {
                'faturados': DataFrame de faturados do mês,
                'conversoes': DataFrame de conversões do mês,
                'ytd': DataFrame de faturados YTD,
                'retencao': DataFrame de retenção de clientes,
                'rentabilidade': DataFrame de rentabilidade histórica
            }
        
        Raises:
            FileNotFoundError: Se arquivos críticos não forem encontrados
            RuntimeError: Se houver erro ao carregar dados
        """
        # 1. Carregar dados via preparar_dados_mensais
        try:
            df_fat, df_conv, df_ytd, df_ret = preparar_dados_mensais.prepare_dataframes_for_month(
                mes, ano, data_path=self.base_path
            )
        except TypeError:
            # Fallback se data_path não for suportado
            df_fat, df_conv, df_ytd, df_ret = preparar_dados_mensais.prepare_dataframes_for_month(
                mes, ano
            )
        except Exception as e:
            raise RuntimeError(f"Erro ao carregar dados mensais via preparar_dados_mensais: {e}")
        
        # Garantir que são DataFrames
        df_fat = df_fat if isinstance(df_fat, pd.DataFrame) else pd.DataFrame()
        df_conv = df_conv if isinstance(df_conv, pd.DataFrame) else pd.DataFrame()
        df_ytd = df_ytd if isinstance(df_ytd, pd.DataFrame) else pd.DataFrame()
        df_ret = df_ret if isinstance(df_ret, pd.DataFrame) else pd.DataFrame()
        
        # 2. Carregar rentabilidade histórica
        df_rentab = self._load_rentabilidade_historica(mes, ano)
        
        return {
            'faturados': df_fat,
            'conversoes': df_conv,
            'ytd': df_ytd,
            'retencao': df_ret,
            'rentabilidade': df_rentab
        }
    
    def _load_rentabilidade_historica(self, mes: int, ano: int) -> pd.DataFrame:
        """
        Carrega arquivo de rentabilidade histórica.
        
        Busca na ordem:
        1. rentabilidade_{MM}_{AAAA}_agrupada.xlsx
        2. rentabilidade_{MM}_{AAAA}_agrupada.csv
        
        Args:
            mes: Mês (1-12)
            ano: Ano
        
        Returns:
            DataFrame com rentabilidade ou DataFrame vazio se não encontrar
        """
        # Nomes dos arquivos
        rent_xlsx = f"rentabilidade_{mes:02d}_{ano}_agrupada.xlsx"
        rent_csv = f"rentabilidade_{mes:02d}_{ano}_agrupada.csv"
        
        rent_path_xlsx = os.path.join(self.rentabilidades_path, rent_xlsx)
        rent_path_csv = os.path.join(self.rentabilidades_path, rent_csv)
        
        # Tentar carregar Excel
        if os.path.exists(rent_path_xlsx):
            try:
                df = pd.read_excel(rent_path_xlsx, engine='openpyxl')
                return df
            except Exception as e:
                print(f"[AVISO] Erro ao carregar {rent_xlsx}: {e}")
        
        # Tentar carregar CSV
        if os.path.exists(rent_path_csv):
            try:
                df = pd.read_csv(rent_path_csv, sep=';')
                return df
            except Exception as e:
                print(f"[AVISO] Erro ao carregar {rent_csv}: {e}")
        
        # Não encontrou - retornar vazio
        print(f"[AVISO] Rentabilidade histórica não encontrada para {mes:02d}/{ano}")
        return pd.DataFrame()
    
    def check_data_availability(self, mes: int, ano: int) -> Dict[str, bool]:
        """
        Verifica disponibilidade de dados sem carregar.
        
        Útil para validar antes de processar reconciliação.
        
        Args:
            mes: Mês
            ano: Ano
        
        Returns:
            Dicionário com disponibilidade:
            {
                'faturados': bool,
                'conversoes': bool,
                'ytd': bool,
                'retencao': bool,
                'rentabilidade': bool
            }
        """
        availability = {}
        
        # Verificar rentabilidade (única que verificamos explicitamente)
        rent_xlsx = f"rentabilidade_{mes:02d}_{ano}_agrupada.xlsx"
        rent_csv = f"rentabilidade_{mes:02d}_{ano}_agrupada.csv"
        rent_path_xlsx = os.path.join(self.rentabilidades_path, rent_xlsx)
        rent_path_csv = os.path.join(self.rentabilidades_path, rent_csv)
        
        availability['rentabilidade'] = os.path.exists(rent_path_xlsx) or os.path.exists(rent_path_csv)
        
        # Outros dados são gerados pelo preparar_dados_mensais
        # Assumimos disponíveis se Analise_Comercial_Completa existir
        analise_path = os.path.join(self.base_path, 'Analise_Comercial_Completa.csv')
        analise_xlsx = os.path.join(self.base_path, 'Analise_Comercial_Completa.xlsx')
        analise_available = os.path.exists(analise_path) or os.path.exists(analise_xlsx)
        
        availability['faturados'] = analise_available
        availability['conversoes'] = analise_available
        availability['ytd'] = analise_available
        availability['retencao'] = analise_available
        
        return availability
    
    def get_available_months(self) -> list:
        """
        Lista meses/anos com rentabilidade disponível.
        
        Returns:
            Lista de tuplas (mes, ano) ordenadas
        """
        if not os.path.exists(self.rentabilidades_path):
            return []
        
        available = []
        
        try:
            for filename in os.listdir(self.rentabilidades_path):
                # Padrão: rentabilidade_MM_AAAA_agrupada.xlsx ou .csv
                if filename.startswith('rentabilidade_') and '_agrupada' in filename:
                    parts = filename.replace('rentabilidade_', '').replace('_agrupada', '').split('_')
                    if len(parts) >= 2:
                        try:
                            mes = int(parts[0])
                            ano = int(parts[1])
                            if 1 <= mes <= 12 and 2000 <= ano <= 2100:
                                available.append((mes, ano))
                        except ValueError:
                            continue
        except Exception:
            pass
        
        # Ordenar por ano e mês
        available.sort(key=lambda x: (x[1], x[0]))
        
        return available

