<!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8">
    <base href="/" />
    <style type="text/css">
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
    }

    .wrapper {
        width: 100%;
        margin: 100px 0 0;
        text-align: center;
    }

    .login_panle {
        display: block;
        width: 570px;
        text-align: center;
        font-size: 14px;
        vertical-align: middle;
        color: #666;
        margin: 0 auto;
    }

    .login_panle p {
        margin: 5px 0;
        line-height: 14px;
    }

    .qr_panle {
        display: inline-block;
        width: 100px;
        height: 100px;
        overflow: hidden;
    }

    .qrcode {
        display: inline-block;
        vertical-align: top;
        width: 100px;
        height: 100px;
        margin: 0 auto;
        background: url('/static/img/progress.gif') center center no-repeat;
        cursor: pointer;
    }

    .login_success,
    .qr_invalid {
        display: none;
        vertical-align: top;
        position: relative;
        top: -100px;
        width: 100px;
        height: 100px;
        margin-bottom: -100px;
        text-align: center;
        background: rgba(0, 0, 0, .25);
        cursor: pointer;
    }

    .login_success .fa,
    .qr_invalid .fa {
        display: inline-block;
        height: 100px;
        overflow: hidden;
        font-size: 60px;
        line-height: 100px;
        overflow: hidden;
    }

    .login_success .fa-check {
        color: #74C328;
    }

    .qr_invalid .fa-refresh {
        color: #F39800;
    }

    .tips {
        color: #000;
    }

    .group_list {
        display: block;
        width: 570px;
        text-align: left;
        font-size: 14px;
        vertical-align: middle;
        color: #666;
        margin: 0 auto;
    }

    .group_list {
        display: block;
        width: 570px;
        text-align: left;
        font-size: 14px;
        color: #666;
        margin: 50px auto;
    }

     .group_list span {
        display: block;
        width: 100%;
    }

    .group_list ul {
        font-size: 12px;
        list-style: none;
        padding: 0;
    }

    .group_list ul li {
        display: inline-block;
        width: 190px;
        height: 30px;
        text-overflow: ellipsis;
        white-space: nowrap;
        overflow: hidden;
        cursor: pointer;
    }

    .group_list ul li:hover {
        color: #0366d6;
    }

    .group_list ul li img {
        width: 18px;
    }
    </style>
    <link href="https://cdn.bootcss.com/font-awesome/4.7.0/css/font-awesome.min.css" rel="stylesheet" type="text/css">
    <script type="text/javascript" src="/static/js/jquery.min.js?v=3.2.1"></script>
    <link href="/static/favicon.ico" rel="shortcut icon" type="image/x-icon" />
    <title>QQ Group Members (v0.1.0)</title>
</head>

<body>
    <div class="wrapper">
        <div class="login_panle">
            <div id="qr_panle" class="qr_panle">
                <img id="qrcode" class="qrcode" src="" alt="" title="点击可刷新" onclick="qrRefresh()" />
                <span id="login_success" class="login_success" onclick="qrRefresh()">
                    <i class="fa fa-check" aria-hidden="true" title="登录成功"></i>
                </span>
                <span id="qr_invalid" class="qr_invalid" onclick="qrRefresh()">
                    <i class="fa fa-refresh" aria-hidden="true" title="二维码失效，请点击刷新"></i>
                </span>
            </div>
            <p id="tips" class="tips">手机 QQ 扫描二维码</p>
        </div>
        <div id="group_list" class="group_list">
        </div>
    </div>
    <a href="https://github.com/caspartse/QQ-Group-Members" target="_blank"><img style="position: absolute; top: 0; right: 0; border: 0;" src="/static/img/forkme_right_green_007200.png" alt="Fork me on GitHub" data-canonical-src="https://s3.amazonaws.com/github/ribbons/forkme_right_green_007200.png"></a>
    <script type='text/javascript'>
        function gMembers(gc) {
            $.ajax({
                type: 'POST',
                url: '/qgmems/gmembers',
                data: 'gc=' + gc,
                success: function(obj) {
                    var path = '/qgmems/download?rid=' + obj;
                    window.open(path, '_blank');
                }
            });
        }

        function displayGList() {
            var url = '/qgmems/glist?t=' + (new Date().getTime());
            $.ajax({
                url: url,
                cache: false,
                dataType: 'html',
                success: function(obj) {
                    $('#group_list').empty();
                    $('#group_list').append(obj);
                }
            });
        }

        function changeStatus(status) {
            switch (status) {
                case 0:
                    $('#tips').text('手机 QQ 扫描二维码');
                    break;
                case 1:
                    $('#tips').text('二维码认证中...');
                    break;
                case 2:
                    $('#login_success').css('display', 'inline-block');
                    $('#tips').text('登录成功');
                    displayGList();
                    break;
                case 3:
                    $('#qr_invalid').css('display', 'inline-block');
                    $('#tips').text('二维码失效，请点击刷新');
                    break;
                default:
                    console.log(status);
            }
        }

        function loginQuery() {
            function trigger() {
                var url = '/qgmems/qrlogin?t=' + (new Date().getTime());
                $.ajax({
                    url: url,
                    cache: false,
                    dataType: 'json',
                    success: function(obj) {
                        var status = JSON.parse(JSON.stringify(obj)).status;
                        changeStatus(status);
                        if ([2, 3].includes(status)) {
                            clearInterval(window.queryTimmer);
                        }
                    }
                });
            }
            window.queryTimmer = setInterval(trigger, 2000);
        }

        function qrRefresh() {
            $('#group_list').empty();
            clearInterval(window.queryTimmer);
            $('#qrcode').attr('src', '');
            var src = '/qgmems/qrshow?t=' + (new Date().getTime());
            $('#qrcode').attr('src', src);
            $('#login_success').css('display', 'none');
            $('#qr_invalid').css('display', 'none');
            $('#tips').text('手机 QQ 扫描二维码');
            loginQuery();
        }

        (function() {
            qrRefresh();
        })();
    </script>
</body>

</html>