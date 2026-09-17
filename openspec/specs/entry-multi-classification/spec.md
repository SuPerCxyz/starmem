# entry-multi-classification Specification

## Purpose
支持一条 Entry 同时拥有多个内容分类，使日志、决策、命令、配置等混合内容不再被强制压缩成单一类型；保留主分类以兼容既有读取、检索与展示路径，并允许用户人工编辑分类集合且不被 AI 重跑覆盖。

## Requirements
### Requirement: 一条 Entry 多分类

系统 SHALL 允许一条 Entry 保存多个内容分类，并保留 `content_type` 作为主分类以保持向后兼容。

#### Scenario: AI 判定的多分类
- **WHEN** AI 或规则判定一条 Entry 同时属于多个类型
- **THEN** 系统保存全部类型，主分类仍可被单独读取

#### Scenario: 人工编辑多分类
- **WHEN** 用户在多分类编辑器中增删类型
- **THEN** 系统保存用户来源的分类集合，且 AI 重跑不覆盖用户修改

#### Scenario: 按类型检索
- **WHEN** 用户按某一类型过滤或搜索
- **THEN** 包含该类型（不限于主分类）的 Entry 均应命中

#### Scenario: 向后兼容
- **WHEN** 既有数据只有单一 `content_type`
- **THEN** 读取多分类时返回包含该主分类的集合，不要求数据迁移回填

