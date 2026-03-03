# Django Tree Comments vs Django Contrib Comments

## 完整功能对比分析

> 对比日期: 2026-03-01
> 对比版本:
> - django-tree-comments: 0.0.4
> - django-contrib-comments: 2.2.0

---

## 一、核心代码差异（Core Code Differences）

### 1.1 模型层差异

| 特性 | django-contrib-comments | django-tree-comments |
|------|------------------------|---------------------|
| 父评论支持 | ❌ 无 | ✅ `parent` 字段支持嵌套评论 |
| GenericForeignKey | ✅ | ✅ |
| Site 关联 | ✅ | ✅ |
| 用户关联 | ✅ | ✅ |
| is_public/is_removed | ✅ | ✅ |
| CommentFlag 模型 | ✅ 具体类 | ✅ AbstractCommentFlag (可交换) |
| 模型交换性 | ✅ COMMENTS_APP | ✅ TREE_COMMENTS_COMMENT_MODEL |

**django-tree-comments 新增字段/方法：**
```python
# AbstractComment 新增
parent = models.ForeignKey(..., related_name="children")  # 父评论
get_reply_url()  # 获取回复 URL

# CommentManager 新增方法
visible()       # 获取可见评论
roots()         # 获取根评论
cte_for_instance()     # CTE 树形查询
threaded_for_instance()  # 线程化评论列表
```

### 1.2 视图层差异

| 特性 | django-contrib-comments | django-tree-comments |
|------|------------------------|---------------------|
| 架构风格 | 函数视图 (FBV) | 类视图 (CBV) |
| post_comment | ✅ 函数 | ✅ CommentPostView |
| flag/delete/approve | ✅ 函数 | ✅ FlagView/DeleteView/ApproveView |
| 表单获取视图 | ❌ 无 | ✅ CommentFormTemplateView |
| 回复视图 | ❌ 无 | ✅ ReplyView |
| JSON 响应支持 | ❌ 有限 | ✅ Accept header + as_json() |
| HTML 片段响应 | ❌ 无 | ✅ format=html 参数 |

**django-tree-comments 新增视图：**
```python
CommentFormTemplateView  # GET 获取表单，支持 Accept: application/json
ReplyView                # 回复评论页面
CommentActionRedirectMixin  # 重定向混入类
CommentModerationPermissionMixin  # 权限混入类
```

### 1.3 表单层差异

| 特性 | django-contrib-comments | django-tree-comments |
|------|------------------------|---------------------|
| CommentSecurityForm | ✅ | ✅ |
| CommentDetailsForm | ✅ | ✅ |
| parent 字段 | ❌ 无 | ✅ 支持 |
| as_json() 方法 | ❌ 无 | ✅ 返回 JSON 可序列化字典 |

**django-tree-comments 新增：**
```python
# CommentDetailsForm.__init__ 新增参数
parent=None  # 父评论对象

# CommentDetailsForm 新增方法
as_json()  # 返回表单初始值字典，用于 AJAX
```

---

## 二、对外 API 差异（External API Differences）

### 2.1 公共函数对比

| API 函数 | django-contrib-comments | django-tree-comments |
|----------|------------------------|---------------------|
| `get_model()` | ✅ | ✅ `get_comment_model()` |
| `get_form()` | ✅ | ✅ `get_comment_form()` |
| `get_form_target()` | ✅ | ✅ `get_comment_form_target()` |
| `get_flag_url()` | ✅ | ❌ **缺失** |
| `get_delete_url()` | ✅ | ❌ **缺失** |
| `get_approve_url()` | ✅ | ❌ **缺失** |
| `get_comment_app()` | ✅ | ❌ |
| `get_comment_app_name()` | ✅ | ❌ |
| `get_comment_flag_model()` | ❌ | ✅ **新增** |

### 2.2 需要补充的 API

```python
# django-tree-comments 需要添加的函数
def get_flag_url(comment):
    """获取标记评论的 URL"""
    return reverse("tree-comments-flag", args=(comment.id,))

def get_delete_url(comment):
    """获取删除评论的 URL"""
    return reverse("tree-comments-delete", args=(comment.id,))

def get_approve_url(comment):
    """获取批准评论的 URL"""
    return reverse("tree-comments-approve", args=(comment.id,))
```

---

## 三、模板差异（Template Differences）

### 3.1 模板文件对比

| 模板文件 | django-contrib-comments | django-tree-comments | 状态 |
|----------|------------------------|---------------------|------|
| `base.html` | ✅ | ✅ | 相同 |
| `form.html` | ✅ | ✅ | 相同 |
| `list.html` | ✅ | ✅ | 相同 |
| `preview.html` | ✅ | ✅ | 相同 |
| `400-debug.html` | ✅ | ✅ | 相同 |
| `posted.html` | ✅ | ✅ | 相同 |
| `flag.html` | ✅ | ✅ | 相同 |
| `flagged.html` | ✅ | ✅ | 相同 |
| `delete.html` | ✅ | ✅ | 相同 |
| `deleted.html` | ✅ | ✅ | 相同 |
| `approve.html` | ✅ | ✅ | 相同 |
| `approved.html` | ✅ | ✅ | 相同 |
| **`reply.html`** | ❌ | ✅ | **新增** |
| **`app.html`** | ❌ | ✅ | **新增** |
| **`comment.html`** | ❌ | ✅ | **新增** |

### 3.2 新增模板说明

**reply.html** - 回复评论页面
```django
<!-- 用于渲染回复特定评论的表单 -->
{% extends "tree_comments/base.html" %}
```

**app.html** - 完整评论应用
```django
<!-- 同时渲染评论列表和表单 -->
{% include "tree_comments/list.html" %}
{% include "tree_comments/form.html" %}
```

**comment.html** - 单个评论组件
```django
<!-- 用于 HTMX/AJAX 场景的单条评论渲染 -->
<div class="comment" id="c{{ comment.id }}">
    {{ comment.comment }}
</div>
```

---

## 四、模板标签差异（Template Tag Differences）

### 4.1 模板标签对比

| 标签 | django-contrib-comments | django-tree-comments |
|------|------------------------|---------------------|
| `{% get_comment_count %}` | ✅ | ✅ |
| `{% get_comment_list %}` | ✅ | ✅ |
| `{% get_comment_form %}` | ✅ | ✅ |
| `{% render_comment_list %}` | ✅ | ✅ |
| `{% render_comment_form %}` | ✅ | ✅ |
| `{% comment_form_target %}` | ✅ | ✅ |
| `{% get_comment_permalink %}` | ✅ | ✅ |
| **`{% render_comment_app %}`** | ❌ | ✅ **新增** |

### 4.2 新增模板标签

**render_comment_app** - 一次渲染完整评论应用
```django
{% load tree_comments %}
{% render_comment_app for object %}
```

等价于：
```django
{% render_comment_list for object %}
{% render_comment_form for object %}
```

---

## 五、国际化 / i18n（Internationalization）

### 5.1 语言支持对比

| 项目 | 语言数量 | locale 目录 |
|------|----------|-------------|
| django-contrib-comments | **70+ 语言** | ✅ `django_comments/locale/` |
| django-tree-comments | **0** | ❌ 不存在 |

### 5.2 django-contrib-comments 支持的语言列表

```
af, ar, az, be, bg, bn, bs, ca, cs, cy, da, de, el, en, en_GB, eo, es,
es_AR, es_MX, et, eu, fa, fi, fr, fy, fy_NL, ga, gd, gl, he, hi, hr,
hu, ia, id, is, it, ja, ka, kk, km, kn, ko, kq, lv, mk, ml, mn, mr,
ms, my, nb, ne, nl, nn, no, os, pa, pl, pt, pt_BR, ro, ru, sk, sl,
sq, sr, sr_Latn, sv, sw, ta, te, th, tk, tr, tt, ug, uk, ur, vi,
zh_Hans, zh_Hant
```

### 5.3 需要迁移的文件结构

```
tree_comments/
└── locale/
    ├── <lang>/LC_MESSAGES/
    │   └── django.po    # 翻译文件
    └── ...
```

---

## 六、文档（Documentation）

### 6.1 文档对比

| 文档类型 | django-contrib-comments | django-tree-comments |
|----------|------------------------|---------------------|
| 文档目录 | ✅ `docs/` 完整 | ❌ 无 |
| ReadTheDocs 配置 | ✅ `.readthedocs.yml` | ❌ 无 |
| README | ✅ README.rst | ✅ README.md (内容较少) |
| HISTORY | ✅ HISTORY.rst | ❌ 无 |

### 6.2 django-contrib-comments 文档列表

| 文档 | 内容 | 状态 |
|------|------|------|
| `index.txt` | 文档首页 | ❌ 缺失 |
| `quickstart.txt` | 快速开始指南 | ❌ 缺失 |
| `settings.txt` | 配置项说明 | ❌ 缺失 |
| `models.txt` | 模型文档 | ❌ 缺失 |
| `forms.txt` | 表单文档 | ❌ 缺失 |
| `moderation.txt` | 审核系统文档 | ❌ 缺失 |
| `signals.txt` | 信号文档 | ❌ 缺失 |
| `custom.txt` | 自定义应用文档 | ❌ 缺失 |
| `example.txt` | 示例代码 | ❌ 缺失 |
| `porting.txt` | 从旧版本迁移 | ❌ 缺失 |
| `management_commands.txt` | 管理命令 | ❌ 缺失 |
| `extensions.py` | Sphinx 扩展 | ❌ 缺失 |
| `conf.py` | Sphinx 配置 | ❌ 缺失 |
| `Makefile` | 构建文件 | ❌ 缺失 |
| `make.bat` | Windows 构建 | ❌ 缺失 |

### 6.3 需要创建的文档结构

```
docs/
├── conf.py              # Sphinx 配置
├── index.txt            # 首页
├── quickstart.txt       # 快速开始
├── settings.txt         # 配置项
├── models.txt           # 模型说明
├── forms.txt            # 表单说明
├── moderation.txt       # 审核系统
├── signals.txt          # 信号说明
├── custom.txt           # 自定义应用
├── example.txt          # 使用示例
├── api/                 # API 文档
│   ├── managers.txt     # 管理器 API
│   └── views.txt        # 视图 API
└── .readthedocs.yml     # RTD 配置
```

---

## 七、CI/CD 和测试配置（CI/CD & Testing）

### 7.1 配置文件对比

| 配置 | django-contrib-comments | django-tree-comments |
|------|------------------------|---------------------|
| `tox.ini` | ✅ 多版本测试 | ❌ |
| `setup.cfg` | ✅ flake8 配置 | ❌ |
| `.github/workflows/` | ❌ | ❌ |
| pytest 配置 | ❌ (用 setup.py test) | ✅ `pyproject.toml` |
| Coverage | ❌ | ❌ |

### 7.2 tox.ini 配置示例

```ini
[tox]
envlist =
    py3{8,9,10,11,12}-django{42,50,51}
    py3{10,11,12}-django-main

[testenv]
basepython =
    py38: python3.8
    py39: python3.9
    py310: python3.10
    py311: python3.11
    py312: python3.12
commands = pytest
setenv =
    PYTHONWARNINGS = default
deps =
    django42: Django>=4.2,<5.0
    django50: Django>=5.0,<5.1
    django51: Django>=5.1,<5.2
    django-main: https://github.com/django/django/archive/main.tar.gz
    pytest
    pytest-django
```

### 7.3 需要添加的 GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
        django-version: ['4.2', '5.0', '5.1']
```

---

## 八、包配置（Package Configuration）

### 8.1 配置对比

| 配置项 | django-contrib-comments | django-tree-comments |
|--------|------------------------|---------------------|
| 格式 | `setup.py` | `pyproject.toml` (现代) |
| Python 版本 | 3.7-3.10 | 3.7+ |
| Django 版本 | 3.2, 4.0, 4.1, 4.2 | 未明确说明 |
| 构建工具 | setuptools | hatchling |
| 核心依赖 | Django>=3.2 | django-cte>=1.3.3 |
| 开发依赖 | 无 | pytest, pytest-django, djlint, ruff |

### 8.2 pyproject.toml 改进建议

```toml
[project]
name = "django-tree-comments"
version = "0.0.5"
description = "A Django app for threaded comments using CTE."
requires-python = ">=3.8"
dependencies = [
    "django>=4.2",
    "django-cte>=1.3.3",
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Framework :: Django",
    "Framework :: Django :: 4.2",
    "Framework :: Django :: 5.0",
    "Framework :: Django :: 5.1",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

[project.optional-dependencies]
test = [
    "pytest>=7.0",
    "pytest-django>=4.5",
    "pytest-cov>=4.0",
]
dev = [
    "django-tree-comments[test]",
    "ruff>=0.1.0",
    "djlint>=1.7.0",
]
```

---

## 九、管理命令（Management Commands）

### 9.1 命令对比

| 命令 | django-contrib-comments | django-tree-comments |
|------|------------------------|---------------------|
| `delete_stale_comments` | ✅ | ✅ |

### 9.2 命令功能相同

两个项目都提供了删除过期评论的管理命令，功能一致。

---

## 十、测试结构（Test Structure）

### 10.1 测试文件对比

| 测试文件 | django-contrib-comments | django-tree-comments |
|----------|------------------------|---------------------|
| `test_models.py` | ✅ | ✅ |
| `test_forms.py` | ✅ (`test_comment_form.py`) | ✅ |
| `test_views.py` | ✅ (`test_comment_views.py`) | ✅ |
| `test_templatetags.py` | ✅ | ✅ |
| `test_feeds.py` | ✅ | ✅ |
| `test_moderation.py` | ✅ (`test_moderation_views.py`) | ✅ |
| `test_admin.py` | ❌ | ✅ **新增** |
| `test_managers.py` | ❌ | ✅ **新增** |
| `test_management_commands.py` | ✅ (`test_delete_stale_comments.py`) | ✅ |
| **`test_app_api.py`** | ✅ | ❌ **缺失** |

### 10.2 需要补充的测试

**test_app_api.py** - 自定义应用 API 测试

测试自定义评论应用可以正确覆盖和扩展默认行为：

```python
def test_get_form():
    """测试获取自定义表单"""

def test_get_form_target():
    """测试获取自定义表单目标"""

def test_get_flag_url():
    """测试获取标记 URL"""
```

---

## 十一、设置项（Settings）

### 11.1 配置项对比

| 设置 | django-contrib-comments | django-tree-comments |
|------|------------------------|---------------------|
| `COMMENTS_APP` | ✅ | ❌ (用 TREE_COMMENTS_*) |
| `COMMENT_MAX_LENGTH` | ✅ (默认 3000) | ✅ (默认 3000) |
| `COMMENTS_TIMEOUT` | ✅ (默认 2h) | ✅ (默认 2h) |
| `COMMENTS_HIDE_REMOVED` | ✅ (默认 True) | ✅ (默认 True) |
| `COMMENTS_ALLOW_PROFANITIES` | ✅ (默认 False) | ✅ (默认 False) |
| `PROFANITIES_LIST` | ✅ | ✅ |
| `TREE_COMMENTS_COMMENT_MODEL` | ❌ | ✅ **新增** |
| `TREE_COMMENTS_COMMENT_FLAG_MODEL` | ❌ | ✅ **新增** |
| `TREE_COMMENTS_COMMENT_FORM` | ❌ | ✅ **新增** |

### 11.2 新增设置说明

```python
# settings.py

# 自定义评论模型
TREE_COMMENTS_COMMENT_MODEL = 'myapp.Comment'

# 自定义评论标记模型
TREE_COMMENTS_COMMENT_FLAG_MODEL = 'myapp.CommentFlag'

# 自定义评论表单
TREE_COMMENTS_COMMENT_FORM = 'myapp.forms.CustomCommentForm'
```

---

## 十二、URL 配置（URL Configuration）

### 12.1 URL 模式对比

| URL 模式 | django-contrib-comments | django-tree-comments |
|----------|------------------------|---------------------|
| post comment | `comments-post-comment` | `tree-comments-post-comment` |
| comment done | `comments-comment-done` | `tree-comments-comment-done` |
| flag | `comments-flag` | `tree-comments-flag` |
| flag done | `comments-flag-done` | `tree-comments-flag-done` |
| delete | `comments-delete` | `tree-comments-delete` |
| delete done | `comments-delete-done` | `tree-comments-delete-done` |
| approve | `comments-approve` | `tree-comments-approve` |
| approve done | `comments-approve-done` | `tree-comments-approve-done` |
| url redirect | `comments-url-redirect` | `tree-comments-url-redirect` |
| **form** | ❌ | `tree-comments-form` **新增** |
| **reply** | ❌ | `tree-comments-reply` **新增** |

---

## 总结：需要迁移/补充的功能清单

### 高优先级（High Priority）

- [ ] **i18n 国际化** - 从 django-contrib-comments 迁移 70+ 语言文件
- [ ] **完整文档** - 创建 `docs/` 目录并迁移所有文档
- [ ] **URL 辅助函数** - 添加 `get_flag_url()`, `get_delete_url()`, `get_approve_url()`
- [ ] **`test_app_api.py`** - 添加自定义应用 API 测试
- [ ] **自定义应用文档** - 编写如何自定义评论应用的文档

### 中优先级（Medium Priority）

- [ ] **CI/CD** - 添加 GitHub Actions workflow
- [ ] **tox.ini** - 添加多版本测试配置
- [ ] **ReadTheDocs 配置** - 添加 `.readthedocs.yml`
- [ ] **更多示例** - 完善示例项目文档
- [ ] **CHANGELOG** - 添加版本变更日志

### 低优先级（Nice to Have）

- [ ] **覆盖率报告** - 添加 pytest-cov
- [ ] **pre-commit hooks** - 添加代码质量检查
- [ ] **贡献指南** - CONTRIBUTING.md
- [ ] **安全策略** - SECURITY.md

---

## 架构差异总结

### django-tree-comments 的优势

1. **线程化评论** - 使用 CTE 实现高效的树形查询
2. **类视图** - 更现代的 Django 视图架构
3. **JSON API** - 内置对 AJAX 友好的响应支持
4. **模块化设计** - 使用 pyproject.toml，现代 Python 项目结构
5. **可交换模型** - 更灵活的模型交换机制

### django-contrib-comments 的优势

1. **国际化** - 完整的 70+ 语言支持
2. **文档完善** - 详尽的官方文档
3. **成熟稳定** - 经过多年生产验证
4. **测试覆盖** - 更全面的测试用例
5. **CI 配置** - tox 多版本测试

---

*本文档由 AI 生成，对比日期: 2026-03-01*
