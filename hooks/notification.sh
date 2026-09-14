#!/bin/bash
# Claude Code Notification Hook — 系統級召回
# 觸發：Notification event（Claude 需要使用者輸入，如權限確認）
# 職責分工：本 hook 只做系統召回固定句池（不含稱謂）；
#           任務完成通知的隨機稱謂歸 voice-notification skill（single-source）。
# 對應 rule：載體選擇見 ai-guide/CLAUDE.md（Hook = 確定性保證）

# bounded say：語音系統掛死時 30s 自清，不留孤兒
# （2026-09-14 實例：孤兒 say 佔住 speech 系統，使下一支前景 say 永久阻塞）
# 語義註記：正常播完時 killer 副殼仍存活至 30s 上限才自滅——設計接受（hook 須立即退出，不可 wait；
# codex review 09-14 提出清 guard 建議，因 wait 會阻塞 hook 而不採，見 .review/main.md M4/C2）
_bounded_say() {
    say -v Meijia -r 180 "$1" 2>/dev/null &
    local pid=$!
    ( sleep 30 && kill "$pid" 2>/dev/null ) &
}

INPUT_JSON=$(cat)
MESSAGE=$(echo "$INPUT_JSON" | jq -r '.message // "Claude Code 通知"')
TITLE=$(echo "$INPUT_JSON" | jq -r '.title // "Claude Code"')

echo "📢 [Notification Hook] $(date '+%H:%M:%S'): $TITLE - $MESSAGE"

# 預熱語音引擎（減少初始化延遲）
_bounded_say ""

# 跳過等待輸入的通知（避免煩人）
if [[ "$MESSAGE" == *"Claude is waiting for your input"* ]]; then
    echo "🔇 跳過語音播放 (等待使用者輸入)"
else
    # 固定系統召回句池（不含稱謂 — 稱謂隨機歸 voice-notification skill）
    msgs=(
        '需要你的確認'
        '這裡需要你決定'
        '請看一下'
        '等你回應'
    )
    random_msg="${msgs[RANDOM % ${#msgs[@]}]}"
    echo "🔊 播放語音: $random_msg"
    _bounded_say "$random_msg"
fi
exit 0
