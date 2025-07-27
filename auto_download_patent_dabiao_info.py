from playwright.sync_api import sync_playwright
import argparse
import time
import os

default_username = 'xufeifan'
default_password = 'zhihui@123'
default_login_url = 'https://wzys.publicdi.com/#/'

def auto_login_and_download(login_url, username, password, download_path):
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            accept_downloads=True
        )
        page = context.new_page()
        
        try:
            # 第一步：登录过程
            print(f"🌐 正在访问登录页面: {login_url}")
            page.goto(login_url, wait_until="domcontentloaded", timeout=60000)
            
            # 填写用户名
            username_input = page.wait_for_selector('#user_name', timeout=30000)
            username_input.fill(username)
            
            # 填写密码
            password_input = page.wait_for_selector('input[type="password"]', timeout=30000)
            password_input.fill(password)
            
            # 等待用户输入验证码
            print("="*60)
            print("🖊️ 请手动输入验证码并点击登录按钮")
            print("✅ 登录成功后脚本将自动点击目标按钮")
            print("="*60)
            
            # 等待登录成功（URL变化）
            page.wait_for_url("https://wzys.publicdi.com/#/case/handlerPending", timeout=60000)
            print("✅ 登录成功！进入待处理案件页面")
            
            # 第二步：点击目标按钮
            print("⏳ 等待目标按钮加载...")
            # 更可靠的选择器定位方式
            navigate_button = page.wait_for_selector('div.el-card__body > div > div:nth-child(7) > button', timeout=30000, state="visible")

            # 更安全的高亮显示方式
            page.evaluate('''(selector) => {
                const element = document.querySelector(selector);
                if (element) {
                    element.style.border = "3px solid red";
                    element.style.boxShadow = "0 0 10px yellow";
                    element.style.zIndex = "9999";
                }
            }''', 'div.el-card__body > div > div:nth-child(7) > button')
            print("🔍 已定位到目标按钮，将在3秒后点击...")
            time.sleep(3)  # 给您时间确认
            
            # 点击导航按钮
            print("🖱️ 正在点击导航按钮...")
            with page.expect_navigation():
                navigate_button.click()
            print("✅ 导航成功！")
            
            # 等待页面稳定（防止立即关闭）
            page.wait_for_timeout(2000)
            
            # 第三步：等待目标页面加载
            print("⏳ 等待目标页面加载...")
            page.wait_for_load_state("networkidle", timeout=30000)
            current_url = page.url
            print(f"🌐 当前页面URL: {current_url}")

            # 第四步：定位并点击下载按钮
            print("⏳ 等待下载按钮加载...")
            download_button = page.wait_for_selector(
                '#app > div > div.main > div > div.content > div > div.el-card.box-card.is-always-shadow > div.el-card__header > div > button:nth-child(5)',
                timeout=30000,
                state="visible"
            )

            # 高亮显示下载按钮
            page.evaluate('''(selector) => {
                const element = document.querySelector(selector);
                if (element) {
                    element.style.border = "3px solid green";
                    element.style.boxShadow = "0 0 10px lime";
                }
            }''', '#app > div > div.main > div > div.content > div > div.el-card.box-card.is-always-shadow > div.el-card__header > div > button:nth-child(5)')
            
            print("🔍 已定位到下载按钮，将在3秒后点击...")
            time.sleep(3)

            # 设置下载监听器
            print("📥 准备导出案件表格...")
            with page.expect_download() as download_info:
                download_button.click()
                print("🖱️ 正在导出案件表格...")
            
            # 获取下载对象
            download = download_info.value

            # 等待导出完成
            print("⏳ 等待导出完成...")
            download_path_object = download.path()
            print(f"✅ 导出完成！临时文件路径: {download_path_object}")

            # 获取建议的文件名
            suggested_filename = download.suggested_filename
            print(f"📄 文件名: {suggested_filename}")

            # 保存文件到指定路径
            final_path = os.path.join(download_path, suggested_filename)
            download.save_as(final_path)

            print(f"💾 文件已保存到: {final_path}")
            print(f"📂 文件大小: {os.path.getsize(final_path)/1024:.2f} KB")
            
            # 第五步：处理表格
            print("="*60)
            print("⏳ 等待表格加载...")
            table_selector = '#app > div > div.main > div > div.content > div > div.el-card.box-card.is-always-shadow > div.el-card__body > div > div.el-card.box-card.is-always-shadow > div > div > div.el-table.el-table--fit.el-table--border.el-table--scrollable-x.el-table--enable-row-transition.configurationTable > div.el-table__body-wrapper.is-scrolling-left > table'

            # 获得表格头
            print("🔍 定位专利类型列...")
            header_selector = '.el-table__header thead tr'
            header_row = page.wait_for_selector(header_selector, timeout=30000)
            header_cells = header_row.query_selector_all('th')
            patent_type_index = None
            patent_name_index = None
            for idx, cell in enumerate(header_cells):
                cell_text = cell.inner_text().strip()
                if cell_text == "专利类型":
                    patent_type_index = idx + 1  # nth-child索引从1开始
                    print(f"✅ 找到专利类型列：第 {patent_type_index} 列")
                elif cell_text == "案件名称":
                    patent_name_index = idx + 1 
                    print(f"✅ 找到专利名称：第 {patent_name_index} 列")

            # 获取行数
            row_count = page.evaluate('''() => {
                return document.querySelectorAll('.el-table__fixed-right tbody tr').length;
            }''')
            print(f"📊 找到 {row_count} 行数据")

            for i in range(1, row_count + 1):
                try:
                    print(f"\n🔍 处理第 {i}/{row_count} 行...")

                    # 获取专利类型及名称
                    patent_type = "N/A"
                    patent_name = "N/A"
                    # 主表格区域选择器
                    main_row_selector = f'{table_selector} tbody tr:nth-child({i})'
                    main_row = page.wait_for_selector(main_row_selector, state="attached")
                    type_cell_selector = f'td:nth-child({patent_type_index})'
                    type_cell = main_row.wait_for_selector(type_cell_selector, state="attached")
                    patent_type = type_cell.inner_text().strip()
                    name_cell_selector = f'td:nth-child({patent_name_index})'
                    name_cell = main_row.wait_for_selector(name_cell_selector, state="attached")
                    patent_name = name_cell.inner_text().strip()
                    print(f"📝 专利类型: {patent_type}")
                    print(f"📝 专利名称: {patent_name}")

                    # 滚动到行居中显示
                    page.evaluate('''(index) => {
                        const row = document.querySelector(
                            `.el-table__body-wrapper tbody tr:nth-child(${index})`
                        );
                        if (row) row.scrollIntoView({block: "center"});
                    }''', i)
                    page.wait_for_timeout(500)
                    
                    # 使用固定列区域定位查看按钮    
                    view_button_selector = (f'div.el-table__fixed-right tbody tr:nth-child({i}) a:first-child')
                    # 等待按钮可见
                    view_button = page.wait_for_selector(view_button_selector, timeout=15000, state="visible")

                    if not view_button:
                        print("⚠️ 未找到查看按钮，跳过")
                        continue

                    # 高亮显示按钮
                    view_button.evaluate('''button => {
                        button.style.border = "2px solid blue";
                        button.style.boxShadow = "0 0 8px cyan";
                        button.style.zIndex = "9999";
                    }''')
                    page.wait_for_timeout(300)
                    
                    # 点击查看按钮
                    print("🖱️ 点击查看按钮...")
                    try:
                        # 先尝试正常点击
                        view_button.click(timeout=5000)
                    except:
                        print("⚠️ 正常点击失败，尝试JavaScript点击")
                        page.evaluate('''(button) => {button.click();}''', view_button)
                    
                    # 等待弹窗出现
                    print("⏳ 等待弹窗加载...")
                    dialog_selector = '#app > div > div.main > div > div.content > div > div.case-detail-container > div > div'
                    dialog = page.wait_for_selector(dialog_selector, timeout=15000, state="visible")

                    # 高亮弹窗
                    page.evaluate('''(selector) => {
                        const dialog = document.querySelector(selector);
                        if (dialog) {
                            dialog.style.border = "3px solid orange";
                            dialog.style.boxShadow = "0 0 15px gold";
                        }
                    }''', dialog_selector)
                    print("✅ 弹窗已打开")
                    
                    # 下载五书合并pdf，命名为专利名称，根据专利类型保存到"{download_path}/design"或"{download_path}/invention"
                    file_header_selector = '#app-root-3 > div:nth-child(3) > div.el-table__header-wrapper > table thead tr'
                    file_header_row = dialog.wait_for_selector(file_header_selector, timeout=30000)
                    file_header_cells = file_header_row.query_selector_all('th')
                    file_type_index = None
                    operate_index = None
                    for idx, cell in enumerate(file_header_cells):
                        cell_text = cell.inner_text().strip()
                        if cell_text == "文件类型":
                            file_type_index = idx + 1
                            print(f"✅ 找到文件类型：第 {file_type_index} 列")
                        if cell_text == "操作":
                            operate_index = idx + 1
                            print(f"✅ 找到操作：第 {operate_index} 列")

                    # 创建保存目录
                    if patent_name != "N/A":
                        save_dir = os.path.join(download_path, "design" if patent_type == "外观设计" else "invention")
                        os.makedirs(save_dir, exist_ok=True)
                        file_table_selector = '#app-root-3 > div:nth-child(3) > div.el-table__body-wrapper.is-scrolling-none > table'
                        file_row_count = dialog.evaluate('''() => {return document.querySelectorAll('#app-root-3 > div:nth-child(3) > div.el-table__body-wrapper.is-scrolling-none > table tbody tr').length;}''')
                        print(f"📊 找到 {file_row_count} 行文件")
                        for j in range(1, file_row_count + 1):
                            file_type = "N/A"
                            file_main_row_selector = f'{file_table_selector} tbody tr:nth-child({j})'
                            file_main_row = dialog.wait_for_selector(file_main_row_selector, state="attached")
                            file_type_cell_selector = f'td:nth-child({file_type_index})'
                            file_type_cell = file_main_row.wait_for_selector(file_type_cell_selector, state="attached")
                            file_type = file_type_cell.inner_text().strip()
                            if file_type == "专利文件五书合并PDF":
                                download_button_selector = f'td:nth-child({operate_index}) > div > div > a:nth-child(2)'
                                # 尝试定位下载按钮
                                download_button = file_main_row.query_selector(download_button_selector)
                                try:
                                    if download_button:
                                        # 高亮下载按钮
                                        download_button.evaluate('''button => {
                                            button.style.border = "2px solid green";
                                            button.style.boxShadow = "0 0 8px lime";
                                        }''')
                                        print("✅ 找到下载按钮")
                                        # 设置下载路径
                                        save_path = os.path.join(save_dir, f"{patent_name}.pdf")
                                        
                                        # 使用Playwright的下载功能
                                        with page.expect_download() as download_info:
                                            # 点击下载按钮
                                            download_button.click()
                                            print(f"📥 正在下载: {patent_name}.pdf")
                                        
                                        # 等待下载完成
                                        download = download_info.value
                                        download.save_as(save_path)
                                        
                                        print(f"💾 文件已保存到: {save_path}")
                                        print(f"📂 文件大小: {os.path.getsize(save_path)/1024:.2f} KB")
                                    else:
                                        print("⚠️ 未找到下载按钮")
                                except Exception as e:
                                    print(f"❌ 下载失败: {e}")
                                    # 保存错误截图
                                    page.screenshot(path=f"download_error_row_{i}.png")
                                    print(f"📷 错误截图已保存: download_error_row_{i}.png")
                    else:
                        print("⚠️ 无法下载: 专利名称为空")
                    
                    # 关闭弹窗
                    close_button_selector = '#app > div > div.main > div > div.content > div > div.case-detail-container > div > div > div.el-dialog__header > button > i'
                    close_button = page.query_selector(close_button_selector)
                    if close_button:
                        close_button.scroll_into_view_if_needed()
                        page.wait_for_timeout(500)
                        # 高亮关闭按钮
                        close_button.evaluate('''button => {
                            button.style.border = "2px solid red";
                            button.style.boxShadow = "0 0 5px pink";
                        }''')
                        print("🚪 点击关闭按钮...")
                        close_button.click()
                    
                    # 等待弹窗关闭
                    page.wait_for_selector(dialog_selector, state="hidden", timeout=5000)
                    print("✅ 弹窗已关闭")
                    
                    # 等待1秒恢复页面状态
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"❌ 处理第 {i} 行时出错: {e}")
                    # 尝试关闭弹窗
                    try:
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(1000)
                    except:
                        pass
                    continue
            
            print("="*60)
            print(f"✅ 表格处理完成！共处理 {row_count} 行")
            print("🛑 按回车键关闭浏览器...")
            
        except Exception as e:
            print(f"❌ 发生错误: {e}")
            print("💡 可能的原因及解决方案：")
            print("1. 按钮未及时加载 - 尝试增加等待时间")
            print("2. 页面结构变化 - 重新检查选择器")
            print("3. 网络问题 - 检查网络连接")
            
            # 保存截图帮助调试
            page.screenshot(path="error_screenshot.png")
            print("📷 错误截图已保存: error_screenshot.png")
        finally:
            # 保持浏览器打开
            input()
            browser.close()

def create_directory(path):
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"📂 创建目录: {path}")
    return path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='自动登录网站并下载打标信息')
    parser.add_argument('--login_url', type=str, default=default_login_url, required=False, help='登录页面URL')
    parser.add_argument('--username', type=str, default=default_username, required=False, help='用户名')
    parser.add_argument('--password', type=str, default=default_password, required=False, help='密码')
    parser.add_argument('--download_path', type=str, required=True, help='文件保存路径')
    
    args = parser.parse_args()
     
    auto_login_and_download(login_url=args.login_url, username=args.username, password=args.password, download_path=args.download_path)