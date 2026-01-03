#!/usr/bin/env python3
"""
Google Dork Scanner v3.0 - Remodelado
======================================
Dois modos:
1. MANUAL - Links clicáveis no terminal
2. SERPER.DEV - API automática com KPI dashboard

Autor: Security Tools
Data: 2025
"""

import os
import sys
import json
import time
import http.client
from datetime import datetime
from urllib.parse import quote_plus

class Colors:
    """Cores ANSI"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class DorkScanner:
    def __init__(self):
        self.config_file = os.path.join(os.path.expanduser("~"), ".dork_scanner_config.json")
        self.api_key = None
        self.domain = None
        self.results = []
        self.stats = {
            'total': 0,
            'with_results': 0,
            'without_results': 0,
            'errors': 0
        }
    
    def clear_screen(self):
        """Limpa tela"""
        os.system('clear')
    
    def print_banner(self):
        """Banner"""
        banner = f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║           🔍 GOOGLE DORK SCANNER v3.0 🔍                        ║
║                                                                  ║
║              Ferramenta de Auditoria de Segurança               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝{Colors.ENDC}
"""
        print(banner)
    
    def load_config(self):
        """Carrega configuração salva"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('api_key')
            except:
                return None
        return None
    
    def save_config(self, api_key):
        """Salva API key"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump({'api_key': api_key}, f)
            os.chmod(self.config_file, 0o600)  # Permissões seguras
            return True
        except:
            return False
    
    def show_menu(self):
        """Menu principal"""
        self.clear_screen()
        self.print_banner()
        
        print(f"{Colors.YELLOW}{'═' * 70}{Colors.ENDC}")
        print(f"{Colors.BOLD}                    ESCOLHA O MODO DE OPERAÇÃO{Colors.ENDC}")
        print(f"{Colors.YELLOW}{'═' * 70}{Colors.ENDC}\n")
        
        print(f"{Colors.GREEN}[1]{Colors.ENDC} 🔗 {Colors.BOLD}MODO MANUAL{Colors.ENDC}")
        print(f"    • Gera links clicáveis no terminal")
        print(f"    • Clique direto para abrir no Google")
        print(f"    • Sem automação - você verifica manualmente")
        print(f"    • {Colors.GREEN}✓ ZERO bloqueio{Colors.ENDC}")
        print(f"    • {Colors.GREEN}✓ Grátis ilimitado{Colors.ENDC}\n")
        
        print(f"{Colors.CYAN}[2]{Colors.ENDC} 🚀 {Colors.BOLD}MODO SERPER.DEV API{Colors.ENDC}")
        print(f"    • Busca automática usando Serper.dev")
        print(f"    • Dashboard com KPIs e estatísticas")
        print(f"    • Salva APENAS resultados encontrados")
        print(f"    • {Colors.GREEN}✓ 2,500 buscas GRÁTIS/mês{Colors.ENDC}")
        print(f"    • {Colors.GREEN}✓ ZERO bloqueio garantido{Colors.ENDC}\n")
        
        print(f"{Colors.RED}[0]{Colors.ENDC} ❌ {Colors.BOLD}SAIR{Colors.ENDC}\n")
        
        print(f"{Colors.YELLOW}{'═' * 70}{Colors.ENDC}")
        
        while True:
            choice = input(f"\n{Colors.BOLD}Escolha [0-2]: {Colors.ENDC}").strip()
            
            if choice == '0':
                print(f"\n{Colors.CYAN}Encerrando...{Colors.ENDC}\n")
                sys.exit(0)
            elif choice in ['1', '2']:
                return int(choice)
            else:
                print(f"{Colors.RED}Opção inválida!{Colors.ENDC}")
    
    def get_api_key(self):
        """Obtém API key (salva ou nova)"""
        saved_key = self.load_config()
        
        if saved_key:
            self.clear_screen()
            self.print_banner()
            print(f"\n{Colors.GREEN}✓ API Key encontrada!{Colors.ENDC}\n")
            print(f"{Colors.CYAN}API Key salva: {saved_key[:20]}...{saved_key[-10:]}{Colors.ENDC}\n")
            
            choice = input(f"{Colors.BOLD}Usar esta API Key? (s/n): {Colors.ENDC}").strip().lower()
            
            if choice == 's':
                self.api_key = saved_key
                return True
        
        # Pedir nova API key
        self.clear_screen()
        self.print_banner()
        
        print(f"\n{Colors.CYAN}╔══════════════════════════════════════════════════════════════════╗")
        print(f"║               CONFIGURAÇÃO DA API SERPER.DEV                     ║")
        print(f"╚══════════════════════════════════════════════════════════════════╝{Colors.ENDC}\n")
        
        print(f"{Colors.YELLOW}Para usar o Modo API:{Colors.ENDC}")
        print(f"1. Acesse: {Colors.CYAN}https://serper.dev{Colors.ENDC}")
        print(f"2. Crie uma conta (grátis)")
        print(f"3. Copie sua API Key do dashboard")
        print(f"4. Cole aqui\n")
        
        print(f"{Colors.GREEN}✓ 2,500 buscas GRÁTIS por mês{Colors.ENDC}")
        print(f"{Colors.GREEN}✓ A API Key será salva para próximas execuções{Colors.ENDC}\n")
        
        api_key = input(f"{Colors.BOLD}Cole sua API Key: {Colors.ENDC}").strip()
        
        if not api_key or len(api_key) < 20:
            print(f"\n{Colors.RED}API Key inválida!{Colors.ENDC}")
            time.sleep(2)
            return False
        
        # Salvar
        if self.save_config(api_key):
            print(f"\n{Colors.GREEN}✓ API Key salva com sucesso!{Colors.ENDC}")
            self.api_key = api_key
            time.sleep(1)
            return True
        else:
            print(f"\n{Colors.YELLOW}⚠ Não foi possível salvar (continuando sem salvar){Colors.ENDC}")
            self.api_key = api_key
            time.sleep(1)
            return True
    
    def get_domain(self):
        """Solicita domínio"""
        self.clear_screen()
        self.print_banner()
        
        print(f"\n{Colors.CYAN}╔══════════════════════════════════════════════════════════════════╗")
        print(f"║                      DOMÍNIO ALVO                                ║")
        print(f"╚══════════════════════════════════════════════════════════════════╝{Colors.ENDC}\n")
        
        print(f"{Colors.RED}⚠️  AVISO LEGAL:{Colors.ENDC}")
        print(f"Use apenas em sistemas que você {Colors.BOLD}POSSUI{Colors.ENDC} ou tem")
        print(f"{Colors.BOLD}AUTORIZAÇÃO EXPLÍCITA{Colors.ENDC} para testar.\n")
        
        while True:
            domain = input(f"{Colors.BOLD}Digite o domínio (ex: exemplo.com): {Colors.ENDC}").strip()
            
            if not domain:
                print(f"{Colors.RED}Domínio não pode ser vazio!{Colors.ENDC}")
                continue
            
            # Limpar
            domain = domain.replace('http://', '').replace('https://', '')
            domain = domain.replace('www.', '').strip('/')
            
            if '.' in domain:
                self.domain = domain
                break
            else:
                print(f"{Colors.RED}Domínio inválido!{Colors.ENDC}")
    
    def load_dorks(self):
        """Carrega lista completa de dorks"""
        # Tentar carregar do JSON
        if os.path.exists('dorks_database.json'):
            try:
                with open('dorks_database.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                dorks = {}
                for category, info in data['dork_categories'].items():
                    dorks[info['description']] = [
                        dork.replace('{domain}', self.domain) 
                        for dork in info['dorks']
                    ]
                return dorks
            except:
                pass
        
        # Lista padrão expandida
        return {
            "Painéis Administrativos": [
                f"site:{self.domain} inurl:admin",
                f"site:{self.domain} inurl:administrator",
                f"site:{self.domain} inurl:moderator",
                f"site:{self.domain} inurl:login",
                f"site:{self.domain} intitle:\"admin panel\"",
                f"site:{self.domain} intitle:\"login page\"",
                f"site:{self.domain} inurl:wp-admin",
                f"site:{self.domain} inurl:wp-login",
                f"site:{self.domain} inurl:phpmyadmin",
                f"site:{self.domain} inurl:cpanel",
                f"site:{self.domain} inurl:webadmin",
                f"site:{self.domain} inurl:admincp",
                f"site:{self.domain} inurl:dashboard",
                f"site:{self.domain} inurl:controlpanel",
            ],
            "Arquivos Sensíveis": [
                f"site:{self.domain} filetype:sql",
                f"site:{self.domain} filetype:env",
                f"site:{self.domain} filetype:log",
                f"site:{self.domain} filetype:bak",
                f"site:{self.domain} filetype:old",
                f"site:{self.domain} filetype:conf",
                f"site:{self.domain} filetype:config",
                f"site:{self.domain} ext:txt intext:password",
                f"site:{self.domain} filetype:xls inurl:password",
                f"site:{self.domain} filetype:xlsx inurl:password",
                f"site:{self.domain} ext:ini intext:password",
                f"site:{self.domain} filetype:dat",
            ],
            "Diretórios Expostos": [
                f"site:{self.domain} intitle:\"index of\"",
                f"site:{self.domain} intitle:\"index of\" backup",
                f"site:{self.domain} intitle:\"index of\" config",
                f"site:{self.domain} intitle:\"index of\" password",
                f"site:{self.domain} intitle:\"index of\" \".git\"",
                f"site:{self.domain} intitle:\"index of\" admin",
                f"site:{self.domain} intitle:\"index of\" database",
                f"site:{self.domain} intitle:\"index of\" \"parent directory\"",
            ],
            "Git e Controle de Versão": [
                f"site:{self.domain} inurl:\".git\"",
                f"site:{self.domain} intitle:\"index of\" \".git\"",
                f"site:{self.domain} inurl:\"/.git/config\"",
                f"site:{self.domain} inurl:\".svn\"",
                f"site:{self.domain} inurl:\"/.git/HEAD\"",
            ],
            "Páginas de Login": [
                f"site:{self.domain} inurl:signin",
                f"site:{self.domain} inurl:signup",
                f"site:{self.domain} inurl:register",
                f"site:{self.domain} intitle:\"login\"",
                f"site:{self.domain} intitle:\"sign in\"",
            ],
            "Arquivos de Configuração": [
                f"site:{self.domain} ext:xml inurl:config",
                f"site:{self.domain} filetype:ini",
                f"site:{self.domain} filetype:cfg",
                f"site:{self.domain} ext:conf",
                f"site:{self.domain} inurl:web.config",
            ],
            "WordPress": [
                f"site:{self.domain} inurl:wp-content",
                f"site:{self.domain} inurl:wp-includes",
                f"site:{self.domain} inurl:wp-config.php",
                f"site:{self.domain} inurl:wp-config.php.bak",
                f"site:{self.domain} inurl:wp-content/uploads",
            ],
            "Banco de Dados": [
                f"site:{self.domain} ext:sql",
                f"site:{self.domain} ext:db",
                f"site:{self.domain} ext:mdb",
                f"site:{self.domain} inurl:database",
            ],
            "Arquivos de Backup": [
                f"site:{self.domain} ext:bak",
                f"site:{self.domain} ext:backup",
                f"site:{self.domain} ext:old",
                f"site:{self.domain} ext:zip",
                f"site:{self.domain} ext:tar.gz",
                f"site:{self.domain} ext:sql.gz",
            ],
        }
    
    def run_manual_mode(self, dorks):
        """Modo Manual - Links clicáveis"""
        self.clear_screen()
        self.print_banner()
        
        print(f"\n{Colors.CYAN}╔══════════════════════════════════════════════════════════════════╗")
        print(f"║                  🔗 MODO MANUAL - LINKS CLICÁVEIS                ║")
        print(f"╚══════════════════════════════════════════════════════════════════╝{Colors.ENDC}\n")
        
        print(f"{Colors.GREEN}✓ Domínio: {Colors.BOLD}{self.domain}{Colors.ENDC}")
        
        total = sum(len(v) for v in dorks.values())
        print(f"{Colors.GREEN}✓ Total de dorks: {Colors.BOLD}{total}{Colors.ENDC}\n")
        
        print(f"{Colors.YELLOW}{'═' * 70}{Colors.ENDC}")
        print(f"{Colors.BOLD}INSTRUÇÕES:{Colors.ENDC}")
        print(f"• Clique nos links abaixo para abrir no navegador")
        print(f"• Ctrl+Clique ou Command+Clique (dependendo do terminal)")
        print(f"• Verifique manualmente cada resultado no Google")
        print(f"{Colors.YELLOW}{'═' * 70}{Colors.ENDC}\n")
        
        current = 0
        
        for category, dork_list in dorks.items():
            print(f"\n{Colors.GREEN}{'▼' * 35}{Colors.ENDC}")
            print(f"{Colors.GREEN}{Colors.BOLD}▶ {category.upper()} ({len(dork_list)} dorks){Colors.ENDC}")
            print(f"{Colors.GREEN}{'▼' * 35}{Colors.ENDC}\n")
            
            for i, dork in enumerate(dork_list, 1):
                current += 1
                url = f"https://www.google.com/search?q={quote_plus(dork)}"
                
                # Link clicável
                print(f"{Colors.CYAN}[{current}/{total}]{Colors.ENDC} {dork}")
                print(f"    {Colors.BLUE}{Colors.UNDERLINE}{url}{Colors.ENDC}\n")
        
        print(f"\n{Colors.GREEN}{'═' * 70}{Colors.ENDC}")
        print(f"{Colors.GREEN}{Colors.BOLD}✓ {total} links gerados com sucesso!{Colors.ENDC}")
        print(f"{Colors.GREEN}{'═' * 70}{Colors.ENDC}\n")
        
        print(f"{Colors.CYAN}Dica: Role para cima para ver todos os links{Colors.ENDC}\n")
        
        input(f"{Colors.BOLD}Pressione ENTER para voltar ao menu...{Colors.ENDC}")
    
    def search_serper(self, dork):
        """Busca usando Serper.dev"""
        try:
            conn = http.client.HTTPSConnection("google.serper.dev")
            
            payload = json.dumps({
                "q": dork,
                "num": 10,
                "gl": "br",
                "hl": "pt"
            })
            
            headers = {
                'X-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            }
            
            conn.request("POST", "/search", payload, headers)
            res = conn.getresponse()
            data = res.read()
            
            if res.status == 200:
                results = json.loads(data.decode("utf-8"))
                
                urls = []
                for item in results.get("organic", []):
                    urls.append({
                        'title': item.get('title', ''),
                        'link': item.get('link', ''),
                        'snippet': item.get('snippet', '')
                    })
                
                return True, urls
            else:
                return False, []
                
        except Exception as e:
            return None, []
    
    def show_dashboard(self):
        """Dashboard com KPIs"""
        self.clear_screen()
        self.print_banner()
        
        print(f"\n{Colors.CYAN}╔══════════════════════════════════════════════════════════════════╗")
        print(f"║                     📊 DASHBOARD - RESULTADOS                    ║")
        print(f"╚══════════════════════════════════════════════════════════════════╝{Colors.ENDC}\n")
        
        # KPIs principais
        print(f"{Colors.YELLOW}{'═' * 70}{Colors.ENDC}")
        print(f"{Colors.BOLD}                         KPIs PRINCIPAIS{Colors.ENDC}")
        print(f"{Colors.YELLOW}{'═' * 70}{Colors.ENDC}\n")
        
        total = self.stats['total']
        with_results = self.stats['with_results']
        without_results = self.stats['without_results']
        errors = self.stats['errors']
        
        success_rate = (with_results / total * 100) if total > 0 else 0
        completion_rate = ((with_results + without_results) / total * 100) if total > 0 else 0
        
        # Linha 1
        print(f"  {Colors.CYAN}Total Testado:{Colors.ENDC}     {Colors.BOLD}{total}{Colors.ENDC} dorks")
        print(f"  {Colors.GREEN}✓ COM Resultados:{Colors.ENDC}  {Colors.BOLD}{Colors.GREEN}{with_results}{Colors.ENDC} dorks")
        print(f"  {Colors.YELLOW}✗ SEM Resultados:{Colors.ENDC}  {Colors.BOLD}{without_results}{Colors.ENDC} dorks")
        if errors > 0:
            print(f"  {Colors.RED}⚠ Erros:{Colors.ENDC}          {Colors.BOLD}{errors}{Colors.ENDC} dorks")
        
        print(f"\n  {Colors.CYAN}Taxa de Descoberta:{Colors.ENDC} {Colors.BOLD}{success_rate:.1f}%{Colors.ENDC}")
        print(f"  {Colors.CYAN}Taxa de Conclusão:{Colors.ENDC}  {Colors.BOLD}{completion_rate:.1f}%{Colors.ENDC}\n")
        
        # Barra de progresso visual
        bar_length = 50
        filled = int(bar_length * with_results / total) if total > 0 else 0
        empty = bar_length - filled
        
        bar = f"{Colors.GREEN}{'█' * filled}{Colors.YELLOW}{'░' * empty}{Colors.ENDC}"
        print(f"  Progresso: {bar} {completion_rate:.0f}%\n")
        
        print(f"{Colors.YELLOW}{'═' * 70}{Colors.ENDC}\n")
        
        # Resultados encontrados
        if with_results > 0:
            print(f"{Colors.GREEN}{'═' * 70}{Colors.ENDC}")
            print(f"{Colors.GREEN}{Colors.BOLD}✓✓✓ DORKS COM RESULTADOS ENCONTRADOS ✓✓✓{Colors.ENDC}")
            print(f"{Colors.GREEN}{'═' * 70}{Colors.ENDC}\n")
            
            # Agrupar por categoria
            by_category = {}
            for result in self.results:
                if result['has_results']:
                    cat = result['category']
                    if cat not in by_category:
                        by_category[cat] = []
                    by_category[cat].append(result)
            
            # Exibir por categoria
            for category, items in by_category.items():
                print(f"\n{Colors.GREEN}▼▼▼ {category.upper()} ({len(items)} dorks) ▼▼▼{Colors.ENDC}\n")
                
                for i, item in enumerate(items, 1):
                    print(f"{Colors.GREEN}{Colors.BOLD}  ✓ [{i}] {item['dork']}{Colors.ENDC}")
                    print(f"{Colors.GREEN}      📍 {len(item['urls'])} URL(s) encontrada(s):{Colors.ENDC}")
                    
                    for url_data in item['urls'][:3]:  # Mostrar até 3
                        print(f"{Colors.GREEN}        • {url_data['link']}{Colors.ENDC}")
                    
                    if len(item['urls']) > 3:
                        print(f"{Colors.YELLOW}        ... e mais {len(item['urls']) - 3} URL(s){Colors.ENDC}")
                    print()
            
            print(f"\n{Colors.GREEN}{'═' * 70}{Colors.ENDC}")
            print(f"{Colors.GREEN}{Colors.BOLD}TOTAL: {with_results} dork(s) com resultados!{Colors.ENDC}")
            print(f"{Colors.GREEN}{'═' * 70}{Colors.ENDC}\n")
        else:
            print(f"{Colors.GREEN}{'═' * 70}{Colors.ENDC}")
            print(f"{Colors.GREEN}{Colors.BOLD}✓✓✓ EXCELENTE! ✓✓✓{Colors.ENDC}")
            print(f"{Colors.GREEN}{'═' * 70}{Colors.ENDC}\n")
            print(f"{Colors.GREEN}Nenhum dork retornou resultados!{Colors.ENDC}")
            print(f"{Colors.GREEN}Isso indica boa segurança ou ausência de exposições.{Colors.ENDC}\n")
        
        # Informação sobre sem resultados
        if without_results > 0:
            print(f"{Colors.CYAN}ℹ️  Informação: {without_results} dork(s) não encontraram resultados{Colors.ENDC}")
            print(f"{Colors.CYAN}   (Isso é uma boa notícia de segurança){Colors.ENDC}\n")
        
        input(f"\n{Colors.BOLD}Pressione ENTER para continuar...{Colors.ENDC}")
    
    def run_serper_mode(self, dorks):
        """Modo Serper.dev - Busca automática"""
        self.clear_screen()
        self.print_banner()
        
        print(f"\n{Colors.CYAN}╔══════════════════════════════════════════════════════════════════╗")
        print(f"║                 🚀 MODO SERPER.DEV - SCAN AUTOMÁTICO             ║")
        print(f"╚══════════════════════════════════════════════════════════════════╝{Colors.ENDC}\n")
        
        print(f"{Colors.GREEN}✓ Domínio: {Colors.BOLD}{self.domain}{Colors.ENDC}")
        
        total = sum(len(v) for v in dorks.values())
        print(f"{Colors.GREEN}✓ Total de dorks: {Colors.BOLD}{total}{Colors.ENDC}")
        print(f"{Colors.CYAN}✓ API: Serper.dev{Colors.ENDC}\n")
        
        print(f"{Colors.YELLOW}Executando scan...{Colors.ENDC}\n")
        
        self.stats['total'] = total
        current = 0
        
        for category, dork_list in dorks.items():
            print(f"\n{Colors.CYAN}▶ {category}{Colors.ENDC}")
            print(f"{Colors.CYAN}{'─' * 70}{Colors.ENDC}")
            
            for dork in dork_list:
                current += 1
                
                print(f"{Colors.CYAN}[{current}/{total}]{Colors.ENDC} {dork[:50]}...", end=' ', flush=True)
                
                has_results, urls = self.search_serper(dork)
                
                if has_results is True and urls:
                    print(f"{Colors.GREEN}✓ {len(urls)} resultado(s){Colors.ENDC}")
                    self.stats['with_results'] += 1
                    self.results.append({
                        'category': category,
                        'dork': dork,
                        'has_results': True,
                        'urls': urls
                    })
                elif has_results is False:
                    print(f"{Colors.YELLOW}✗ Sem resultados{Colors.ENDC}")
                    self.stats['without_results'] += 1
                else:
                    print(f"{Colors.RED}⚠ Erro{Colors.ENDC}")
                    self.stats['errors'] += 1
                
                time.sleep(0.5)  # Pequeno delay
        
        print(f"\n\n{Colors.GREEN}✓ Scan completo!{Colors.ENDC}\n")
        time.sleep(1)
        
        # Mostrar dashboard
        self.show_dashboard()
        
        # Salvar
        if self.stats['with_results'] > 0:
            self.save_results()
    
    def save_results(self):
        """Salva resultados"""
        self.clear_screen()
        self.print_banner()
        
        print(f"\n{Colors.CYAN}╔══════════════════════════════════════════════════════════════════╗")
        print(f"║                         💾 SALVAR RELATÓRIO                      ║")
        print(f"╚══════════════════════════════════════════════════════════════════╝{Colors.ENDC}\n")
        
        choice = input(f"{Colors.BOLD}Deseja salvar o relatório? (s/n): {Colors.ENDC}").strip().lower()
        
        if choice != 's':
            print(f"\n{Colors.YELLOW}Relatório não salvo.{Colors.ENDC}\n")
            return
        
        # Nome do arquivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f"scan_{self.domain}_{timestamp}.txt"
        
        print(f"\n{Colors.CYAN}Nome sugerido:{Colors.ENDC} {default_name}")
        filename = input(f"{Colors.BOLD}Nome do arquivo (Enter = usar sugerido): {Colors.ENDC}").strip()
        
        if not filename:
            filename = default_name
        
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        # Diretório
        print(f"\n{Colors.CYAN}Diretório atual:{Colors.ENDC} {os.getcwd()}")
        custom_dir = input(f"{Colors.BOLD}Outro diretório (Enter = usar atual): {Colors.ENDC}").strip()
        
        if custom_dir and os.path.isdir(custom_dir):
            filepath = os.path.join(custom_dir, filename)
        else:
            filepath = filename
        
        # Salvar
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Cabeçalho
                f.write("=" * 80 + "\n")
                f.write("GOOGLE DORK SCAN REPORT - SERPER.DEV API\n")
                f.write("=" * 80 + "\n")
                f.write(f"Domínio: {self.domain}\n")
                f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"API: Serper.dev\n")
                f.write("=" * 80 + "\n\n")
                
                # Estatísticas
                f.write("ESTATÍSTICAS\n")
                f.write("-" * 80 + "\n")
                f.write(f"Total de dorks testados: {self.stats['total']}\n")
                f.write(f"Dorks COM resultados: {self.stats['with_results']}\n")
                f.write(f"Dorks SEM resultados: {self.stats['without_results']}\n")
                if self.stats['errors'] > 0:
                    f.write(f"Erros: {self.stats['errors']}\n")
                f.write("=" * 80 + "\n\n")
                
                # Nota
                f.write("IMPORTANTE:\n")
                f.write("Este relatório contém APENAS os dorks que ENCONTRARAM resultados.\n")
                f.write("=" * 80 + "\n\n")
                
                # Resultados
                results_by_cat = {}
                for result in self.results:
                    if result['has_results']:
                        cat = result['category']
                        if cat not in results_by_cat:
                            results_by_cat[cat] = []
                        results_by_cat[cat].append(result)
                
                f.write("RESULTADOS ENCONTRADOS\n")
                f.write("=" * 80 + "\n\n")
                
                for category, items in results_by_cat.items():
                    f.write(f"\n{'=' * 80}\n")
                    f.write(f"CATEGORIA: {category}\n")
                    f.write(f"Dorks com resultados: {len(items)}\n")
                    f.write(f"{'=' * 80}\n\n")
                    
                    for i, item in enumerate(items, 1):
                        f.write(f"[{i}] {item['dork']}\n")
                        f.write(f"    Total de URLs: {len(item['urls'])}\n\n")
                        
                        for url_data in item['urls']:
                            f.write(f"    • {url_data['link']}\n")
                            if url_data.get('title'):
                                f.write(f"      Título: {url_data['title']}\n")
                        
                        f.write(f"    {'-' * 76}\n\n")
                
                # Rodapé
                f.write("\n" + "=" * 80 + "\n")
                f.write("FIM DO RELATÓRIO\n")
                f.write("=" * 80 + "\n")
            
            print(f"\n{Colors.GREEN}✓ Relatório salvo com sucesso!{Colors.ENDC}\n")
            print(f"{Colors.CYAN}Arquivo:{Colors.ENDC} {filepath}")
            print(f"{Colors.CYAN}Tamanho:{Colors.ENDC} {os.path.getsize(filepath)} bytes")
            print(f"{Colors.CYAN}Resultados:{Colors.ENDC} {self.stats['with_results']} dork(s) com hits\n")
            
        except Exception as e:
            print(f"\n{Colors.RED}✗ Erro ao salvar: {e}{Colors.ENDC}\n")
        
        input(f"{Colors.BOLD}Pressione ENTER para voltar ao menu...{Colors.ENDC}")
    
    def run(self):
        """Execução principal"""
        while True:
            # Menu
            mode = self.show_menu()
            
            # Obter API key se modo Serper
            if mode == 2:
                if not self.get_api_key():
                    continue
            
            # Obter domínio
            self.get_domain()
            
            # Carregar dorks
            dorks = self.load_dorks()
            
            # Resetar estatísticas
            self.results = []
            self.stats = {
                'total': 0,
                'with_results': 0,
                'without_results': 0,
                'errors': 0
            }
            
            # Executar modo
            if mode == 1:
                self.run_manual_mode(dorks)
            elif mode == 2:
                self.run_serper_mode(dorks)

def main():
    try:
        scanner = DorkScanner()
        scanner.run()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Operação cancelada pelo usuário.{Colors.ENDC}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Erro: {e}{Colors.ENDC}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
