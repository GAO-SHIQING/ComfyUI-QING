/**
 * 节点对齐工具 - 图标定义
 */

export const ALIGNMENT_ICONS = {
    '上对齐': `
        <path d="M200 200 L824 200 M280 280 L380 280 L380 480 L280 480 Z M462 280 L562 280 L562 580 L462 580 Z M644 280 L744 280 L744 680 L644 680 Z" 
              fill="white" stroke="white" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>
    `,
    '下对齐': `
        <path d="M200 824 L824 824 M280 744 L380 744 L380 544 L280 544 Z M462 744 L562 744 L562 444 L462 444 Z M644 744 L744 744 L744 344 L644 344 Z" 
              fill="white" stroke="white" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>
    `,
    '左对齐': `
        <path d="M200 200 L200 824 M280 280 L480 280 L480 380 L280 380 Z M280 462 L580 462 L580 562 L280 562 Z M280 644 L680 644 L680 744 L280 744 Z" 
              fill="white" stroke="white" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>
    `,
    '右对齐': `
        <path d="M824 200 L824 824 M744 280 L544 280 L544 380 L744 380 Z M744 462 L444 462 L444 562 L744 562 Z M744 644 L344 644 L344 744 L744 744 Z" 
              fill="white" stroke="white" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>
    `,
    '水平居中': `
        <path d="M512 200 L512 824 M280 380 L380 380 L380 644 L280 644 Z M644 380 L744 380 L744 644 L644 644 Z" 
              fill="white" stroke="white" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>
    `,
    '垂直居中': `
        <path d="M200 512 L824 512 M380 280 L644 280 L644 380 L380 380 Z M380 644 L644 644 L644 744 L380 744 Z" 
              fill="white" stroke="white" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>
    `,
    '左右拉伸': `
        <path d="M200 512 L824 512 M200 512 L280 450 M200 512 L280 574 M824 512 L744 450 M824 512 L744 574 M350 380 L674 380 L674 644 L350 644 Z" 
              fill="white" stroke="white" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>
    `,
    '上下拉伸': `
        <path d="M512 200 L512 824 M512 200 L450 280 M512 200 L574 280 M512 824 L450 744 M512 824 L574 744 M380 350 L644 350 L644 674 L380 674 Z" 
              fill="white" stroke="white" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>
    `,
    '水平分布': `
        <path d="M220 400 L320 400 L320 624 L220 624 Z M462 400 L562 400 L562 624 L462 624 Z M704 400 L804 400 L804 624 L704 624 Z" 
              fill="white" stroke="white" stroke-width="20" stroke-linejoin="round"/>
        <path d="M340 512 L442 512 M582 512 L684 512" 
              stroke="white" stroke-width="20" stroke-linecap="round"/>
        <path d="M360 490 L340 512 L360 534 M422 490 L442 512 L422 534 M602 490 L582 512 L602 534 M664 490 L684 512 L664 534" 
              fill="none" stroke="white" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>
    `,
    '垂直分布': `
        <path d="M400 220 L624 220 L624 320 L400 320 Z M400 462 L624 462 L624 562 L400 562 Z M400 704 L624 704 L624 804 L400 804 Z" 
              fill="white" stroke="white" stroke-width="20" stroke-linejoin="round"/>
        <path d="M512 340 L512 442 M512 582 L512 684" 
              stroke="white" stroke-width="20" stroke-linecap="round"/>
        <path d="M490 360 L512 340 L534 360 M490 422 L512 442 L534 422 M490 602 L512 582 L534 602 M490 664 L512 684 L534 664" 
              fill="none" stroke="white" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>
    `
};

/**
 * 获取图标SVG
 */
export function getIconSVG(actionName) {
    return ALIGNMENT_ICONS[actionName] || `<circle cx="512" cy="512" r="200" fill="white"/>`;
}

