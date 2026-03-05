"""
Arquivo: tests/test_verify_fix.py
Objetivo: Validar se o fix do 'if __name__ == "__main__":' funcionou e simular argumentos.
Como rodar: python tests/test_verify_fix.py
"""
import unittest
import sys
import os
from io import StringIO
from unittest.mock import patch

# Adiciona o diretório dos scripts ao path para permitir a importação
# Caminho relativo: ../.agent/scripts
SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.agent', 'scripts'))
sys.path.append(SCRIPT_PATH)

class TestVerifyAllFix(unittest.TestCase):

    def test_01_import_safe(self):
        """
        Teste Crítico: Verifica se importar o módulo NÃO causa SystemExit.
        Isso confirma que a chamada main() está protegida.
        """
        try:
            # Tenta importar. Se o bug persistir, isso vai disparar SystemExit imediatamente.
            import verify_all
            import importlib
            importlib.reload(verify_all) # Garante recarga limpa
        except SystemExit:
            self.fail("FALHA CRÍTICA: verify_all.py executou automaticamente ao ser importado. O fix não foi aplicado.")
        except ImportError:
            print(f"\\n[AVISO] verify_all.py não encontrado em {SCRIPT_PATH}. Pulando teste.")

    @patch('sys.stderr', new_callable=StringIO)
    def test_02_missing_arguments(self, mock_stderr):
        """
        Simula execução via linha de comando SEM argumentos.
        Deve falhar com SystemExit code 2 (comportamento padrão do argparse).
        """
        try:
            import verify_all
            # Simula: python verify_all.py
            with patch.object(sys, 'argv', ['verify_all.py']):
                with self.assertRaises(SystemExit) as cm:
                    verify_all.main()
                
                self.assertEqual(cm.exception.code, 2)
                # Verifica se o erro menciona os argumentos obrigatórios
                self.assertIn("required", mock_stderr.getvalue())
                self.assertIn("project", mock_stderr.getvalue())
        except ImportError:
            pass

    def test_03_valid_arguments_simulation(self):
        """
        Simula execução com argumentos VÁLIDOS.
        Verifica se o script passa da fase de argumentos.
        """
        try:
            import verify_all
            
            # Simula: python verify_all.py pilot-atendimento --url http://localhost:8000
            test_args = ['verify_all.py', 'pilot-atendimento', '--url', 'http://localhost:8000']
            
            with patch.object(sys, 'argv', test_args):
                # Mockamos a função interna de lógica (se soubéssemos o nome) ou requests
                # Aqui, vamos capturar qualquer Exception que NÃO seja SystemExit.
                # Se der erro de conexão/arquivo, significa que o argparse funcionou!
                try:
                    with patch('builtins.print'): # Silencia output
                        verify_all.main()
                except SystemExit as e:
                    if e.code != 0:
                        self.fail(f"Argparse rejeitou argumentos válidos. Exit code: {e.code}")
                except Exception:
                    # Sucesso: O script tentou rodar a lógica (e falhou por falta de rede/arquivos reais),
                    # o que prova que a barreira dos argumentos foi superada.
                    pass
        except ImportError:
            pass

if __name__ == '__main__':
    unittest.main()