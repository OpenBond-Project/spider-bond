#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用密码登录服务器并安装本机公钥。

什么时候用它：
  sl.sh boot 依赖 sshpass，而 sshpass 在 Git Bash 下有时无法正确传递
  含 + = 等字符的密码（表现为 Password 被拒，但密码其实是对的）。

用法：
  python bootstrap_ssh.py              # 交互输入密码
  SL_PASS='xxx' python bootstrap_ssh.py  # 非交互（会留在命令历史，不建议）

成功后 sl.sh 的所有命令都可免密使用。
"""
import getpass
import os
import pathlib
import shlex
import sys

try:
    import paramiko
except ImportError:
    sys.exit("缺少 paramiko，请先执行: python -m pip install paramiko")

# 与 sl.sh 保持一致：本地私密配置放 .env.local（已在 .gitignore 中）
_envf = pathlib.Path(__file__).resolve().parent / '.env.local'
if _envf.exists():
    for _line in _envf.read_text(encoding='utf-8').splitlines():
        _line = _line.strip()
        if _line and not _line.startswith('#') and '=' in _line:
            _k, _v = _line.split('=', 1)
            os.environ.setdefault(_k.strip(), _v.strip())

HOST = os.environ.get('SL_HOST', '')
if not HOST:
    raise SystemExit('请设置 SL_HOST=<服务器 IP 或域名>，例如：\n'
                     '  SL_HOST=203.0.113.10 SL_PASS=xxx python bootstrap_ssh.py\n'
                     '也可以先在 .env.local 里配置 SL_HOST。')
USER = os.environ.get('SL_USER', 'root')
KEY = pathlib.Path(os.path.expanduser(os.environ.get('SL_KEY', '~/.ssh/id_ed25519.pub')))


def main():
    if not KEY.exists():
        sys.exit('找不到公钥: %s\n可先执行 ssh-keygen -t ed25519 生成' % KEY)

    pub = KEY.read_text(encoding='utf-8').strip()
    if not pub:
        sys.exit('公钥文件为空: %s' % KEY)

    pw = os.environ.get('SL_PASS')
    if not pw:
        pw = getpass.getpass('%s@%s 密码: ' % (USER, HOST))
    if not pw:
        sys.exit('密码为空，已取消')

    q = shlex.quote(pub)
    remote = (
        'mkdir -p /root/.ssh; chmod 700 /root/.ssh; touch /root/.ssh/authorized_keys; '
        '{ grep -qxF %s /root/.ssh/authorized_keys || echo %s >> /root/.ssh/authorized_keys; }; '
        'sort -u /root/.ssh/authorized_keys -o /root/.ssh/authorized_keys; '
        'chmod 600 /root/.ssh/authorized_keys; '
        'echo PUBKEY_OK; '
        'echo "authorized_keys 行数: $(grep -c . /root/.ssh/authorized_keys)"'
    ) % (q, q)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, port=22, username=USER, password=pw, timeout=15,
                       allow_agent=False, look_for_keys=False,
                       auth_timeout=15, banner_timeout=15)
    except paramiko.AuthenticationException:
        sys.exit('认证失败：密码不正确（或该用户禁止密码登录）')
    except Exception as exc:
        sys.exit('连接失败：%s: %s' % (type(exc).__name__, exc))

    try:
        _, stdout, stderr = client.exec_command(remote, timeout=25)
        out = stdout.read().decode('utf-8', 'ignore').strip()
        err = stderr.read().decode('utf-8', 'ignore').strip()
    finally:
        client.close()

    for line in out.splitlines():
        print('  ' + line)
    if err:
        print('  stderr: ' + err)

    if 'PUBKEY_OK' not in out:
        sys.exit('未确认安装成功，请检查上面的输出')
    print('\n[OK] 公钥已安装，接下来应该可以免密登录了')
    return 0


if __name__ == '__main__':
    sys.exit(main())
