import React from 'react';

interface HeaderProps {
    title: string;
    subtitle?: string;
}

const Header: React.FC<HeaderProps> = ({ title, subtitle }) => {
    return (
        <div className="text-center mb-8">
            <h1 className="text-3xl md:text-4xl font-bold text-primary mb-2">{title}</h1>
            {subtitle && <p className="text-lg text-gray-600">{subtitle}</p>}
        </div>
    );
}

export default Header;