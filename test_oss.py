import oss2
try:
    from core.oss_settings import ALIYUN_OSS_ACCESS_KEY_ID, ALIYUN_OSS_ACCESS_KEY_SECRET
except ImportError:
    # 开发环境默认值（或抛出异常）
    ALIYUN_OSS_ACCESS_KEY_ID = ""
    ALIYUN_OSS_ACCESS_KEY_SECRET = ""

# 填入你的配置
ACCESS_KEY_ID = ALIYUN_OSS_ACCESS_KEY_ID
ACCESS_KEY_SECRET = ALIYUN_OSS_ACCESS_KEY_SECRET
ENDPOINT = "oss-cn-beijing.aliyuncs.com"
BUCKET_NAME = "tm-web-tlias"


def test_upload():
    print(f"正在连接 OSS: {BUCKET_NAME} @ {ENDPOINT}...")

    try:
        # 1. 连接
        auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, f"http://{ENDPOINT}", BUCKET_NAME)

        # 2. 尝试上传一段文本
        file_name = "media/test_upload3.txt"
        content = "Hello from SocialShop!"

        result = bucket.put_object(file_name, content)

        if result.status == 200:
            print("✅ 上传成功！")
            print(f"文件路径: {file_name}")
            print("请去阿里云控制台刷新，看有没有 'media' 文件夹和 'test_upload.txt'")
        else:
            print(f"❌ 上传失败，状态码: {result.status}")

    except Exception as e:
        print(f"❌ 发生错误: {e}")


if __name__ == "__main__":
    test_upload()