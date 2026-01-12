import time
import os
import json
import random
import string
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 从环境变量读取配置
def get_env_config():
    """从环境变量读取所有配置"""
    config = {
        'urls': os.getenv('TEST_URLS', '').split(',') if os.getenv('TEST_URLS') else [],
        'rounds': int(os.getenv('TEST_ROUNDS', '5')),
        'test_duration_min': int(os.getenv('TEST_DURATION_MIN', '15')),
        'test_duration_max': int(os.getenv('TEST_DURATION_MAX', '25')),
        'wait_interval_min': int(os.getenv('WAIT_INTERVAL_MIN', '15')),
        'wait_interval_max': int(os.getenv('WAIT_INTERVAL_MAX', '30')),
        'use_random_ua': os.getenv('USE_RANDOM_UA', 'true').lower() == 'true',
        'custom_ua': os.getenv('CUSTOM_UA', ''),
        'ipv4': os.getenv('IPV4', ''),
        'method': os.getenv('METHOD', 'get').lower(),
        'referer': os.getenv('REFERER', ''),
        'cookies': os.getenv('COOKIES', ''),
        'redirect_num': int(os.getenv('REDIRECT_NUM', '5')),
        'dns_server_type': os.getenv('DNS_SERVER_TYPE', 'isp'),
        'dns_server': os.getenv('DNS_SERVER', ''),
        'enable_lines': os.getenv('ENABLE_LINES', '1,2,3,5').split(','),
        'screenshot': os.getenv('ENABLE_SCREENSHOT', 'false').lower() == 'true',
        'random_suffix_length': int(os.getenv('RANDOM_SUFFIX_LENGTH', '10')),
    }
    return config

USER_AGENT_TEMPLATES = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36 Edg/{edge_version}",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{firefox_version}.0) Gecko/20100101 Firefox/{firefox_version}.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_{mac_version}_{mac_patch}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36",
]

def generate_random_chrome_version():
    """生成随机Chrome版本号"""
    major = random.randint(115, 132)
    minor = random.randint(0, 9)
    patch = random.randint(0, 9999)
    return f"{major}.{minor}.{patch}"

def generate_random_firefox_version():
    """生成随机Firefox版本号"""
    major = random.randint(100, 123)
    minor = random.randint(0, 9)
    return f"{major}.{minor}"

def generate_random_version():
    """生成随机版本号"""
    major = random.randint(100, 130)
    minor = random.randint(0, 9)
    patch = random.randint(0, 9999)
    return f"{major}.{minor}.{patch}"

def generate_random_mac_version():
    """生成随机macOS版本号"""
    major = random.randint(14, 16)
    minor = random.randint(0, 9)
    patch = random.randint(0, 9)
    return f"{major}_{minor}_{patch}"

def generate_random_user_agent():
    """生成随机User-Agent"""
    template = random.choice(USER_AGENT_TEMPLATES)
    
    params = {
        'version': generate_random_chrome_version(),
        'edge_version': generate_random_version(),
        'firefox_version': generate_random_firefox_version(),
        'mac_version': generate_random_mac_version(),
        'mac_patch': random.randint(0, 9)
    }
    
    return template.format(**params)

def append_random_suffix_to_url(url, length=6):
    """在URL后面添加随机英文字母后缀"""
    # 生成随机英文字母
    random_suffix = ''.join(random.choices(string.ascii_letters, k=length))
    
    # 处理URL，在查询参数或末尾添加
    if '?' in url:
        # URL中已有查询参数
        return f"{url}&{random_suffix}={random_suffix}"
    else:
        # 直接添加到URL末尾
        url_with_slash = url if url.endswith('/') else url + '/'
        return f"{url_with_slash}{random_suffix}"

def ensure_result_directory():
    """确保结果目录存在"""
    result_dir = "result"
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
        print(f"创建结果目录: {result_dir}")
    return result_dir

def setup_driver(use_random_ua, custom_ua=''):
    """设置Chrome WebDriver"""
    chrome_options = Options()
    
    # 禁用图片加载
    prefs = {
        'profile.managed_default_content_settings.images': 2,
        'profile.default_content_settings.popups': 0,
    }
    chrome_options.add_experimental_option('prefs', prefs)
    
    # 浏览器设置
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 设置User-Agent
    if use_random_ua:
        user_agent = generate_random_user_agent()
        print(f"使用随机User-Agent: {user_agent[:80]}...")
    else:
        user_agent = custom_ua if custom_ua else generate_random_user_agent()
        print(f"使用指定User-Agent: {user_agent[:80]}...")
    
    chrome_options.add_argument(f'--user-agent={user_agent}')
    
    try:
        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print(f"ChromeDriver初始化失败: {str(e)}")
        raise

def set_form_options(driver, config):
    """设置表单的高级选项"""
    try:
        # 确保表单元素可见和可交互，先等待一下
        time.sleep(0.5)
        
        # 尝试点击高级选项按钮以展开表单
        try:
            advanced_button = driver.find_element(By.ID, "ad_options")
            if advanced_button:
                driver.execute_script("arguments[0].click();", advanced_button)
                print("✓ 点击高级选项按钮以展开表单")
                time.sleep(0.5)
        except:
            print("⚠ 未找到高级选项按钮或已展开")
        
        # 设置指定解析IP
        if config['ipv4']:
            try:
                ipv4_input = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "ipv4"))
                )
                ipv4_input.clear()
                ipv4_input.send_keys(config['ipv4'])
                print(f"✓ 设置指定解析IP: {config['ipv4']}")
            except Exception as e:
                print(f"✗ 设置IPv4失败: {str(e)}")
                try_click_advanced_options(driver)
        
        # 设置方法 (GET/POST)
        if config['method'] == 'post':
            try:
                post_radio = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='method'][value='post']"))
                )
                driver.execute_script("arguments[0].click();", post_radio)
                print("✓ 设置方法: POST")
            except Exception as e:
                print(f"✗ 设置METHOD失败: {str(e)}")
                try_click_advanced_options(driver)
        
        # 设置Referer
        if config['referer']:
            try:
                referer_input = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "referer"))
                )
                referer_input.clear()
                referer_input.send_keys(config['referer'])
                print(f"✓ 设置Referer: {config['referer']}")
            except Exception as e:
                print(f"✗ 设置Referer失败: {str(e)}")
                try_click_advanced_options(driver)
        
        # 设置User-Agent (在表单中)
        try:
            ua_input = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "ua"))
            )
            ua_input.clear()
            
            if config['use_random_ua']:
                random_ua = generate_random_user_agent()
                ua_input.send_keys(random_ua)
                print(f"✓ 表单中设置随机UA: {random_ua[:60]}...")
            elif config['custom_ua']:
                ua_input.send_keys(config['custom_ua'])
                print(f"✓ 表单中设置自定义UA")
        except Exception as e:
            print(f"✗ 设置UA失败: {str(e)}")
            try_click_advanced_options(driver)
        
        # 设置Cookie
        if config['cookies']:
            try:
                cookies_input = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "cookies"))
                )
                cookies_input.clear()
                cookies_input.send_keys(config['cookies'])
                print(f"✓ 设置Cookie")
            except Exception as e:
                print(f"✗ 设置Cookie失败: {str(e)}")
                try_click_advanced_options(driver)
        
        # 设置重定向次数
        try:
            redirect_input = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "redirect_num"))
            )
            redirect_input.clear()
            redirect_input.send_keys(str(config['redirect_num']))
            print(f"✓ 设置重定向次数: {config['redirect_num']}")
        except Exception as e:
            print(f"✗ 设置重定向次数失败: {str(e)}")
            try_click_advanced_options(driver)
        
        # 设置运营商线路
        try:
            time.sleep(0.5)
            checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[name='line']")
            for checkbox in checkboxes:
                value = checkbox.get_attribute('value')
                is_checked = checkbox.is_selected()
                
                if value not in config['enable_lines'] and is_checked:
                    driver.execute_script("arguments[0].click();", checkbox)
                    time.sleep(0.1)
                elif value in config['enable_lines'] and not is_checked:
                    driver.execute_script("arguments[0].click();", checkbox)
                    time.sleep(0.1)
            print(f"✓ 设置运营商线路: {','.join(config['enable_lines'])}")
        except Exception as e:
            print(f"✗ 设置运营商线路失败: {str(e)}")
            try_click_advanced_options(driver)
        
        # 设置DNS
        if config['dns_server_type'] == 'custom' and config['dns_server']:
            try:
                custom_dns_radio = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='dns_server_type'][value='custom']"))
                )
                driver.execute_script("arguments[0].click();", custom_dns_radio)
                time.sleep(0.3)
                dns_input = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "dns_server"))
                )
                dns_input.clear()
                dns_input.send_keys(config['dns_server'])
                print(f"✓ 设置自定义DNS: {config['dns_server']}")
            except Exception as e:
                print(f"✗ 设置DNS失败: {str(e)}")
                try_click_advanced_options(driver)
        
        return True
        
    except Exception as e:
        print(f"✗ 设置表单选项时出错: {str(e)}")
        return False

def try_click_advanced_options(driver):
    """尝试点击高级选项按钮"""
    try:
        advanced_button = driver.find_element(By.ID, "ad_options")
        driver.execute_script("arguments[0].click();", advanced_button)
        print("  → 已点击高级选项按钮")
        time.sleep(0.5)
    except Exception as e:
        print(f"  → 无法点击高级选项: {str(e)}")

def run_speed_test(driver, url, config, test_num):
    """运行单次测速测试"""
    try:
        print(f"\n{'='*70}")
        print(f"测试 #{test_num}: {url}")
        print(f"{'='*70}")
        
        # 第一次访问需要打开网页
        if test_num == 1:
            print("打开测速网站...")
            driver.get("https://www.itdog.cn/http/")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "host"))
            )
            time.sleep(2)
        
        # 设置高级选项
        set_form_options(driver, config)
        
        # 添加随机后缀到URL
        test_url = append_random_suffix_to_url(url, config['random_suffix_length'])
        print(f"输入测试URL: {test_url}")
        host_input = driver.find_element(By.ID, "host")
        host_input.clear()
        host_input.send_keys(test_url)
        time.sleep(0.5)
        
        # 点击快速测试按钮
        print("点击快速测试按钮...")
        fast_button = driver.find_element(By.XPATH, "//button[contains(text(), '快速测试')]")
        driver.execute_script("arguments[0].click();", fast_button)
        
        # 生成随机的测速持续时间
        test_duration = random.randint(config['test_duration_min'], config['test_duration_max'])
        print(f"等待测速完成（预计 {test_duration} 秒）...")
        
        # 等待测速完成
        start_time = time.time()
        for remaining in range(test_duration, 0, -1):
            print(f"\r剩余等待时间: {remaining}秒", end='', flush=True)
            time.sleep(1)
        print()
        
        # 等待结果加载
        time.sleep(2)
        
        # 获取结果
        try:
            result_element = driver.find_element(By.ID, "return_info")
            result = result_element.text
            print(f"✓ 测试完成，结果长度: {len(result)} 字符")
            return result
        except NoSuchElementException:
            print("⚠ 无法找到结果元素")
            return "无法获取测速结果"
            
    except Exception as e:
        print(f"✗ 测试过程中出现错误: {str(e)}")
        return f"错误: {str(e)}"

def save_single_result(result_dir, url, result, round_num, test_num):
    """保存单次测试结果"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_url = url.replace('://', '_').replace('/', '_').replace(':', '_').replace('?', '_')
    filename = f"{result_dir}/test_r{round_num}_t{test_num}_{safe_url}_{timestamp}.txt"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"URL: {url}\n")
            f.write(f"轮次: {round_num}\n")
            f.write(f"序号: {test_num}\n")
            f.write("="*60 + "\n")
            f.write(result + "\n")
        return filename
    except Exception as e:
        print(f"保存结果时出错: {str(e)}")
        return None

def save_summary_result(result_dir, all_results, config):
    """保存汇总结果"""
    summary_file = f"{result_dir}/summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        summary = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'config': {
                'urls': config['urls'],
                'rounds': config['rounds'],
                'test_duration_range': f"{config['test_duration_min']}-{config['test_duration_max']}秒",
                'wait_interval_range': f"{config['wait_interval_min']}-{config['wait_interval_max']}秒",
            },
            'total_tests': len(all_results),
            'results': all_results
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"汇总结果已保存到: {summary_file}")
        return summary_file
    except Exception as e:
        print(f"保存汇总结果时出错: {str(e)}")
        return None

def validate_config(config):
    """验证配置"""
    if not config['urls']:
        print("错误: 未从环境变量TEST_URLS中获取URL")
        return False
    
    config['urls'] = [u.strip() for u in config['urls'] if u.strip()]
    
    if not config['urls']:
        print("错误: URL列表为空")
        return False
    
    if config['use_random_ua'] and config['custom_ua']:
        print("注意: 同时设置了随机UA和自定义UA，优先使用自定义UA")
        config['use_random_ua'] = False
    
    print(f"✓ 配置验证成功")
    print(f"  - URLs: {len(config['urls'])} 个")
    print(f"  - 测试轮次: {config['rounds']}")
    print(f"  - 单轮测速持续时间: {config['test_duration_min']}-{config['test_duration_max']}秒")
    print(f"  - 轮次间隔: {config['wait_interval_min']}-{config['wait_interval_max']}秒")
    print(f"  - 使用随机UA: {config['use_random_ua']}")
    print(f"  - 随机后缀长度: {config['random_suffix_length']} 个字母")
    
    return True

def main():
    print("="*80)
    print("网站测速自动化脚本 v2.0")
    print("="*80)
    
    # 读取配置
    config = get_env_config()
    
    # 验证配置
    if not validate_config(config):
        return
    
    # 准备目录
    result_dir = ensure_result_directory()
    
    # 初始化WebDriver
    try:
        driver = setup_driver(config['use_random_ua'], config['custom_ua'])
    except Exception as e:
        print(f"无法初始化WebDriver: {str(e)}")
        return
    
    all_results = []
    global_test_num = 0
    
    try:
        for round_num in range(1, config['rounds'] + 1):
            print(f"\n{'#'*80}")
            print(f"第 {round_num}/{config['rounds']} 轮测试开始")
            print(f"{'#'*80}")
            
            # 测试每个URL
            for url_idx, url in enumerate(config['urls'], 1):
                global_test_num += 1
                
                result = run_speed_test(driver, url, config, global_test_num)
                
                # 保存单次结果
                saved_file = save_single_result(result_dir, url, result, round_num, global_test_num)
                
                all_results.append({
                    'round': round_num,
                    'test_num': global_test_num,
                    'url': url,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'result_preview': result[:200] if len(result) > 200 else result
                })
                
                if saved_file:
                    print(f"✓ 结果已保存到: {saved_file}")
                
                # 如果不是最后一个URL，等待后进行下一个
                if url_idx < len(config['urls']):
                    print("准备下一个测试...")
                    time.sleep(1)
            
            # 如果不是最后一轮，等待后进行下一轮
            if round_num < config['rounds']:
                wait_time = random.randint(config['wait_interval_min'], config['wait_interval_max'])
                print(f"\n⏳ 第 {round_num} 轮完成，等待 {wait_time} 秒后进行第 {round_num + 1} 轮...")
                
                for remaining in range(wait_time, 0, -1):
                    print(f"\r剩余等待时间: {remaining}秒", end='', flush=True)
                    time.sleep(1)
                print()
        
        # 保存汇总结果
        save_summary_result(result_dir, all_results, config)
        
        # 打印最终统计
        print(f"\n{'='*80}")
        print("✓ 所有测试完成！")
        print(f"  - 总轮次: {config['rounds']}")
        print(f"  - 总测试数: {global_test_num}")
        print(f"  - 结果目录: {result_dir}")
        print(f"{'='*80}")
            
    except KeyboardInterrupt:
        print("\n用户中断测试")
        if all_results:
            save_summary_result(result_dir, all_results, config)
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        if all_results:
            save_summary_result(result_dir, all_results, config)
    finally:
        if 'driver' in locals():
            driver.quit()
            print("浏览器已关闭")

if __name__ == "__main__":
    main()
