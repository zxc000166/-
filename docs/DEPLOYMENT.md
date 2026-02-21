# 部署指南 (Deployment Guide)

本指南介绍如何使用 Docker 和 Docker Compose 部署 **2D 转 3D 转换系统**。

## 前置条件

- [Docker](https://www.docker.com/get-started) (v20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.0+)

## 快速开始

### 1. 构建并启动

在项目根目录下运行以下命令：

```bash
# 构建镜像并后台启动容器
docker-compose up -d --build
```

### 2. 访问应用

启动完成后，打开浏览器访问：

http://localhost:5000

### 3. 查看日志

```bash
# 查看实时日志
docker-compose logs -f
```

### 4. 停止服务

```bash
docker-compose down
```

## 安全与验证策略

本系统已实施生产级的文件上传安全策略：

1.  **文件类型白名单**：允许 `JPG`, `JPEG`, `PNG` 以及 `PLY` 格式。
2.  **内容深度校验**：后端使用 PIL 库校验图片，以及自定义校验器验证 PLY 头信息。
3.  **大小限制**：
    *   单次请求最大：50MB (Flask `MAX_CONTENT_LENGTH`)
    *   单文件最大：50MB (应用层严格校验)
4.  **安全扫描**：集成了病毒扫描钩子（当前为模拟实现，生产环境可接入 ClamAV）。
5.  **文件名清洗**：强制使用 `secure_filename` 清洗文件名。

## 3D 预览功能集成

本系统集成了基于 WebGL (Three.js) 的 PLY 模型在线预览功能。

### 格式支持
- 支持 ASCII 和 Binary 格式的 `.ply` 文件。
- 自动适配模型比例和视角。

### 性能说明
- 文件上传限制已调整为 **50MB**，以支持更大的点云/网格模型。
- 预览功能完全在客户端（浏览器）运行，依赖用户设备的显卡性能。
- 推荐使用 Chrome, Firefox 或 Edge 浏览器以获得最佳 WebGL 性能。

## 目录挂载说明

为了持久化保存上传的文件和生成的 3D 模型，容器内的目录已挂载到宿主机：

- `./uploads` -> `/app/uploads` (上传的图片)
- `./results` -> `/app/results` (生成的 .ply 模型)

## 常见问题

### 镜像体积过大
由于包含了 PyTorch 和 OpenCV，镜像体积可能较大（约 1GB+）。Dockerfile 已配置为使用 CPU 版本的 PyTorch 以最小化体积。

### 端口冲突
如果本地 5000 端口被占用，请修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "8080:5000"  # 将宿主机 8080 映射到容器 5000
```

### 权限问题 (Linux)
如果在 Linux 环境下遇到写入权限问题，请确保宿主机的 `uploads` 和 `results` 目录具有写入权限：

```bash
chmod 777 uploads results
```
