% Section 2 large-deflection beam

clear;
clc;
close all;

numPoints = 150;
numThetaSamples = 500;

K = [0, 0.1, 1, 1.5, 2, 2.5,5,50];
forceAnglesDeg = [9, 27, 45, 63, 81, 99, 117, 135, 153, 171];

figure('Color', 'w', 'Position', [50, 50, 1400, 700]);
tiledlayout(2, 4, 'Padding', 'compact', 'TileSpacing', 'compact');

for i = 1:length(K)
    nexttile;
    hold on;

    for angleDeg = forceAnglesDeg
        phi = deg2rad(angleDeg);

        eps_th = 1e-6;

        if K(i) <= 2
            th_max = min(pi, phi + acos(1 - K(i))) - eps_th;
        else
            th_max = pi - eps_th;
        end
        
        ths = linspace(0.0, th_max, numPoints);

        aL = zeros(size(ths));
        bL = zeros(size(ths));

        for j = 1:length(ths)
            th0 = ths(j);

            if th0 == 0.0
                aL(j) = 1;
                bL(j) = 0;
                continue;
            end

            a = @(t) 0.5 * (1.0 ./ sqrt(cos(th0 - phi) - cos(t - phi) + K(i)));
            sqralp = integral(a, 0, th0);

            x = @(t) (1 / (2 * sqralp)) * (cos(t) ./ sqrt(cos(th0 - phi) - cos(t - phi) + K(i)));
            y = @(t) (1 / (2 * sqralp)) * (sin(t) ./ sqrt(cos(th0 - phi) - cos(t - phi) + K(i)));
            
            
            aL(j) = integral(x, 0, th0);
            bL(j) = integral(y, 0, th0);

            % for k =2:length(aL)
            %     if aL(k) < aL(k-1)
            %         id = k
            % 
            %     end
            % 
            kl = numPoints;
            id = kl;
            if K(i) <2 && K(i) > 0
                
            % dtx = gradient(aL,ths);
            % for k = 1:length(dtx)
            %     if dtx(k) <= 0.05
            %         idx = k;
            %     end
            % end

            dtxx = gradient(gradient(aL, ths), ths);
            thresh = median(abs(dtxx)) + 4*mad(dtxx, 1);
            
            idxx = find(abs(dtxx) > thresh, 1, 'first');
            if isempty(idxx)
                idxx = length(aL);
            end
            
            % dty = gradient(bL,ths);
            % for k = 1:length(dty)
            %     if dty(k) <= 0.05
            %         idy = k;
            %     end
            % end

            dtyy = gradient(gradient(bL, ths), ths);
            thresh = median(abs(dtyy)) + 4*mad(dtyy, 1);
            
            idyy = find(abs(dtyy) > thresh, 1, 'first');
            if isempty(idyy)
                idyy = length(bL);
            end

           
            id = min([idxx,idyy]);

            elseif K(i) == 0
                id = kl-1;
            else
                id = kl;
            end
            

            
            % plot(ths,dt)



        end
       
        plot(aL(1:id), bL(1:id), 'LineWidth', 1.0, 'DisplayName', sprintf('%g deg', angleDeg));

    end

    title(sprintf('load ratio = %g', K(i)));
    xlabel('a / L');
    ylabel('b / L');
    xlim([-0.55, 1.05]);
    ylim([0.0, 1.05]);
    grid on;
    box on;
end

lgd = legend('Location', 'eastoutside');
lgd.Title.String = 'force angle';
sgtitle('Section 2 Trajectory Atlas');
